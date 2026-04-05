import os
import asyncio
import sys
import json
from typing import Any, List, Optional, AsyncGenerator
from dotenv import load_dotenv

from mcp import ClientSession
from mcp.client.sse import sse_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ModelRequest
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import uvicorn

load_dotenv()

from pydantic import BaseModel, Field, ConfigDict
from typing import Union, List, Dict, Any

# --- Models for History ---
class MessageItem(BaseModel):
    model_config = ConfigDict(extra='allow')
    content: Union[str, List[Dict[str, Any]]] = ""
    type: str  # e.g., 'HumanMessage', 'AIMessage', 'ToolMessage'
    tool_calls: List[dict] = Field(default_factory=list)
    tool_call_id: Optional[str] = None  # Required for ToolMessage

class ChatRequest(BaseModel):
    query: str
    history: List[MessageItem] = Field(default_factory=list)
    session_id: str = "default"

class AdaptiveModelSelectorMiddleware(AgentMiddleware):
    def __init__(self, agent: "EventSummaryAgent"):
        self._agent = agent

    async def awrap_model_call(self, request: ModelRequest, handler):
        messages = self._agent._extract_request_messages(request)
        token_count = self._agent._estimate_tokens(messages)
        model = (
            self._agent.high_capacity_model
            if token_count > self._agent.high_token_threshold
            else self._agent.default_model
        )
        return await handler(request.override(model=model))


class EventSummaryAgent:
    """
    A modular agent that connects to an MCP server, loads analytical tools,
    and provides a high-level interface for querying event and vehicle traffic logs.
    """

    def __init__(self, model="gpt-5.4-nano-2026-03-17", temperature=0.5):
        self.model_name = model
        self.temperature = temperature
        self.mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000/sse")
        self.default_model = ChatOpenAI(model=self.model_name, temperature=self.temperature)
        self.high_capacity_model = ChatOpenAI(model="gpt-5.1-2025-11-13", temperature=self.temperature)
        self.llm = self.default_model
        self.agent = None
        self.tools = None

        self._sse_client_ctx = None
        self._client_session: Optional[ClientSession] = None
        self.max_history_messages = self._resolve_history_limit()
        self.high_token_threshold = self._resolve_token_threshold()
        self._token_encoder = None
        self._token_encoder_tried = False

    def _resolve_history_limit(self) -> int:
        try:
            limit = int(os.getenv("EVENT_SUMMARY_AGENT_MAX_HISTORY", "12"))
            return max(2, limit)
        except ValueError:
            return 12

    def _resolve_token_threshold(self) -> int:
        try:
            threshold = int(os.getenv("EVENT_SUMMARY_AGENT_HIGH_TOKEN_THRESHOLD", "250000"))
            return max(50_000, threshold)
        except ValueError:
            return 250000

    def _get_token_encoder(self):
        if self._token_encoder_tried:
            return self._token_encoder
        self._token_encoder_tried = True
        try:
            import tiktoken

            self._token_encoder = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            self._token_encoder = None
        return self._token_encoder

    def _message_to_text(self, message: Any) -> str:
        if isinstance(message, (HumanMessage, AIMessage, ToolMessage)):
            text = message.content or ""
            label = message.__class__.__name__
            return f"{label}: {text}"
        if isinstance(message, dict):
            return f"{message.get('type', '')} {message.get('content', '')}"
        return str(message)

    def _estimate_tokens(self, messages: List[Any]) -> int:
        encoder = self._get_token_encoder()
        total = 0
        for msg in messages:
            raw = self._message_to_text(msg)
            if not raw:
                continue
            if encoder:
                total += len(encoder.encode(raw))
            else:
                total += max(1, len(raw) // 4)
        return total

    def _extract_request_messages(self, request: ModelRequest) -> List[Any]:
        state_messages = getattr(request.state, "messages", None)
        if state_messages is None and isinstance(request.state, dict):
            state_messages = request.state.get("messages", [])
        return list(state_messages or [])

    def _trim_history(self, history: List[MessageItem]) -> List[MessageItem]:
        if len(history) <= self.max_history_messages:
            return history
        return history[-self.max_history_messages:]

    async def initialize(self):
        """
        Explicitly connect to the MCP server, load tools, and create the agent.
        Call this once at startup.
        """
        if self._client_session is not None:
            return

        self._sse_client_ctx = sse_client(self.mcp_url)
        read_write = await self._sse_client_ctx.__aenter__()

        self._client_session = ClientSession(*read_write)
        await self._client_session.__aenter__()
        await self._client_session.initialize()

        self.tools = await load_mcp_tools(self._client_session)

        system_prompt = (
            "You are an expert analytical assistant specializing in security and traffic event logs. "
            "Use the provided tools to retrieve data and provide concise, accurate summaries. "
            "Always prefer structured data (lists/tables) when presenting counts or comparisons."
        )
        self.agent = create_agent(
            self.default_model,
            self.tools,
            system_prompt=system_prompt,
            middleware=[AdaptiveModelSelectorMiddleware(self)],
        )

    async def run_query(
        self,
        user_input: str,
        chat_history: List[MessageItem] = None,
    ) -> AsyncGenerator[str, None]:
        if chat_history is None:
            chat_history = []
        trimmed_history = self._trim_history(chat_history)

        if self.agent is None:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        messages = []

        i = 0
        while i < len(trimmed_history):
            item = trimmed_history[i]

            # HUMAN
            if item.type == "HumanMessage":
                messages.append(HumanMessage(content=item.content))
                i += 1
                continue

            # AI MESSAGE
            if item.type == "AIMessage":
                messages.append(
                    AIMessage(
                        content=item.content or "",
                        tool_calls=item.tool_calls or []
                    )
                )

                if item.tool_calls:
                    expected_ids = [tc["id"] for tc in item.tool_calls]
                    found_ids = []

                    j = i + 1

                    while j < len(trimmed_history) and trimmed_history[j].type == "ToolMessage":
                        tool_item = trimmed_history[j]

                        tool_content = tool_item.content
                        if isinstance(tool_content, list):
                            try:
                                tool_content = " ".join(
                                    t.get("text", "") for t in tool_content if isinstance(t, dict)
                                )
                            except:
                                tool_content = str(tool_content)

                        tool_content = str(tool_content or "[Tool executed successfully]")

                        if "data:image" in tool_content:
                            tool_content = "[Image generated]"
                        elif len(tool_content) > 500:
                            tool_content = tool_content[:500] + "...[truncated]"

                        messages.append(
                            ToolMessage(
                                content=tool_content,
                                tool_call_id=tool_item.tool_call_id
                            )
                        )

                        found_ids.append(tool_item.tool_call_id)
                        j += 1

                    for missing_id in expected_ids:
                        if missing_id not in found_ids:
                            messages.append(
                                ToolMessage(
                                    content="[Auto-generated tool response]",
                                    tool_call_id=missing_id
                                )
                            )

                    i = j
                    continue

                i += 1
                continue

            if item.type == "ToolMessage":
                i += 1
                continue

        messages.append(HumanMessage(content=user_input))

        initial_count = len(messages)
        yielded_ids = set()

        async for chunk in self.agent.astream({"messages": messages}, stream_mode="values"):
            all_messages = chunk["messages"]
            new_messages = all_messages[initial_count:]

            if not new_messages:
                continue

            latest_message = new_messages[-1]

            msg_id = getattr(latest_message, "id", str(len(all_messages)))
            if msg_id in yielded_ids:
                continue
            yielded_ids.add(msg_id)

            payload = {
                "content": latest_message.content,
                "type": latest_message.__class__.__name__,
                "tool_calls": getattr(latest_message, "tool_calls", []),
                "tool_call_id": getattr(latest_message, "tool_call_id", None),
            }

            yield json.dumps(payload) + "\n"

# --- FastAPI Implementation ---
agent_instance = EventSummaryAgent()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await agent_instance.initialize()
    yield
    if agent_instance._client_session:
        await agent_instance._client_session.__aexit__(None, None, None)
    if agent_instance._sse_client_ctx:
        await agent_instance._sse_client_ctx.__aexit__(None, None, None)

app = FastAPI(title="Event Summary Agent API", lifespan=lifespan)

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        return StreamingResponse(
            agent_instance.run_query(request.query, request.history),
            media_type="text/event-stream",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

async def run_standalone_loop():
    if not os.getenv("OPENAI_API_KEY"):
        print("Missing OPENAI_API_KEY in .env file.")
        return

    print("\n=== Analytical Chat Agent (Sub-Agent Ready) ===")
    print("(Type 'exit' or 'quit' to stop)\n")

    await agent_instance.initialize()

    chat_history = []

    while True:
        try:
            user_input = input("You: ")

            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            if not user_input.strip():
                continue

            print("\nThinking...")

            last_content = ""
            last_tool_calls = []

            async for chunk_str in agent_instance.run_query(user_input, chat_history):
                data = json.loads(chunk_str.strip())
                content = data.get("content", "")
                tool_calls = data.get("tool_calls", [])
                msg_type = data.get("type", "")

                if tool_calls:
                    tc_names = [tc["name"] for tc in tool_calls]
                    if tc_names and tc_names != [tc["name"] for tc in last_tool_calls]:
                        print(f"Calling tools: {tc_names}")
                        last_tool_calls = tool_calls

                if content and content != last_content and msg_type == "AIMessage":
                    last_content = content

            print(f"\nAgent: {last_content}\n")

            chat_history.append(MessageItem(content=user_input, type="HumanMessage"))
            chat_history.append(
                MessageItem(content=last_content, type="AIMessage", tool_calls=last_tool_calls)
            )
            chat_history = agent_instance._trim_history(chat_history)

        except EOFError:
            break
        except Exception as e:
            print(f"\nError: {e}\n")

if __name__ == "__main__":
    if True:
        port = 7000
        if "--port" in sys.argv:
            try:
                port_idx = sys.argv.index("--port") + 1
                if port_idx < len(sys.argv):
                    port = int(sys.argv[port_idx])
            except ValueError:
                pass

        print(f"Starting FastAPI server on 127.0.0.1:{port} (reload enabled)...")
        uvicorn.run("event_summary_agent:app", host="127.0.0.1", port=port, reload=True)
    else:
        asyncio.run(run_standalone_loop())
