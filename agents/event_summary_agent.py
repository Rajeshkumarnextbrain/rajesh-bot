import os
import asyncio
import sys
import json
from typing import Any, List, Optional, Tuple, AsyncGenerator, Union
from dotenv import load_dotenv

from mcp import ClientSession
from mcp.client.sse import sse_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# FastAPI imports
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn

load_dotenv()

from pydantic import BaseModel, Field, ConfigDict

# --- Models for History ---
class MessageItem(BaseModel):
    model_config = ConfigDict(extra='allow')
    content: str = ""
    type: str # e.g., 'HumanMessage', 'AIMessage', 'ToolMessage'
    tool_calls: List[dict] = Field(default_factory=list)
    tool_call_id: Optional[str] = None # Required for ToolMessage

class ChatRequest(BaseModel):
    query: str
    history: List[MessageItem] = []
    session_id: str = "default"

class EventSummaryAgent:
    """
    A modular agent that connects to an MCP server, loads analytical tools,
    and provides a high-level interface for querying event and vehicle traffic logs.
    """

    def __init__(self, model="gpt-4o-mini", temperature=0.5):
        self.model_name = model
        self.temperature = temperature
        self.mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000/sse")
        self.llm = ChatOpenAI(model=self.model_name, temperature=self.temperature)
        self.agent = None
        self.tools = None
        
        self._sse_client_ctx = None
        self._client_session: Optional[ClientSession] = None

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
            self.llm, 
            self.tools, 
            system_prompt=system_prompt
        )

    async def run_query(
        self,
        user_input: str,
        chat_history: List[MessageItem] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Runs a query through the agent using streaming.
        Yields JSON string chunks representing the current state of the agent.
        """
        if chat_history is None:
            chat_history = []

        if self.agent is None:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        # Convert structured history to LangChain messages
        messages = []
        for item in chat_history:
            msg_type = item.type
            content = item.content
            tool_calls = item.tool_calls

            if msg_type == "HumanMessage":
                messages.append(HumanMessage(content=content))
            elif msg_type == "ToolMessage":
                messages.append(ToolMessage(content=content, tool_call_id=item.tool_call_id))
            else:
                messages.append(AIMessage(content=content, tool_calls=tool_calls))
        
        messages.append(HumanMessage(content=user_input))

        # Track initial message count to only yield NEW messages
        initial_count = len(messages)
        yielded_ids = set()

        async for chunk in self.agent.astream({"messages": messages}, stream_mode="values"):
            all_messages = chunk["messages"]
            # Only consider messages added after our input
            new_messages = all_messages[initial_count:]
            if not new_messages:
                continue
                
            latest_message = new_messages[-1]
            
            # Use message ID if available, otherwise fallback to index in full list
            msg_id = getattr(latest_message, "id", str(len(all_messages)))
            if msg_id in yielded_ids:
                continue
            yielded_ids.add(msg_id)

            payload = {
                "content": latest_message.content,
                "type": latest_message.__class__.__name__,
                "tool_calls": getattr(latest_message, "tool_calls", []),
                "tool_call_id": getattr(latest_message, "tool_call_id", None)
            }
            yield json.dumps(payload) + "\n"

# --- FastAPI Implementation ---
agent_instance = EventSummaryAgent()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the agent once on startup
    await agent_instance.initialize()
    yield
    # Cleanup logic to close MCP session cleanly
    if agent_instance._client_session:
        await agent_instance._client_session.__aexit__(None, None, None)
    if agent_instance._sse_client_ctx:
        await agent_instance._sse_client_ctx.__aexit__(None, None, None)

app = FastAPI(title="Event Summary Agent API", lifespan=lifespan)

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint for frontend integration using streaming SSE-like output.
    Now accepts structured history objects!
    """
    try:
        return StreamingResponse(
            agent_instance.run_query(request.query, request.history),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# --- CLI Implementation ---
async def run_standalone_loop():
    """
    Main entry point for CLI usage.
    """
    if not os.getenv("OPENAI_API_KEY"):
        print("Missing OPENAI_API_KEY in .env file.")
        return

    print("\n=== Analytical Chat Agent (Sub-Agent Ready) ===")
    print("(Type 'exit' or 'quit' to stop)\n")
    
    # Initialize the agent for CLI usage
    await agent_instance.initialize()
    
    chat_history = [] # Now stores MessageItem-like structures

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
                    # Basic mechanism to only print each tool call once per stream
                    tc_names = [tc['name'] for tc in tool_calls]
                    if tc_names and tc_names != [tc['name'] for tc in last_tool_calls]:
                        print(f"Calling tools: {tc_names}")
                        last_tool_calls = tool_calls
                
                if content and content != last_content:
                    if msg_type == "AIMessage":
                        last_content = content
            
            print(f"\nAgent: {last_content}\n")
            
            # Store history in the same format the API uses
            chat_history.append(MessageItem(content=user_input, type="HumanMessage"))
            chat_history.append(MessageItem(content=last_content, type="AIMessage", tool_calls=last_tool_calls))

        except EOFError:
            break
        except Exception as e:
            print(f"\nError: {e}\n")

if __name__ == "__main__":
    # Check for --api flag or fallback to CLI
    if True:
        # Default port to 7000 but allow overriding via --port
        port = 7000
        if "--port" in sys.argv:
            try:
                port_idx = sys.argv.index("--port") + 1
                if port_idx < len(sys.argv):
                    port = int(sys.argv[port_idx])
            except ValueError:
                pass
        
        print(f"Starting FastAPI server on 127.0.0.1:{port} (reload enabled)...")
        # Use string import to support hot-reload
        uvicorn.run("event_summary_agent:app", host="127.0.0.1", port=port, reload=True)
    else:
        asyncio.run(run_standalone_loop())
