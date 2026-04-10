import os
import asyncio
from dotenv import load_dotenv

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

load_dotenv()

async def initize_mcp():
    mcp_client = MultiServerMCPClient(
        {
            'attendance':{
                "transport": "sse",
                "url": os.getenv("ATTENDANCE_MCP_URL", "http://localhost:8000/sse"),
                } 
            }
        )

    tools = await mcp_client.get_tools()

    filtered_tools = [
        t for t in tools 
        if t.name in ["get_staffs", "get_attendances_advanced", "get_attendance_logs",'get_current_time']
    ]

    return filtered_tools


class AttendanceAgent:
    def __init__(self, primary_model=None, temperature=0.5):
        self.primary_model_name = primary_model or os.getenv("PRIMARY_MODEL", "gpt-5.4-nano-2026-03-17")
        self.model = ChatOpenAI(
            model=self.primary_model_name,
            temperature=temperature,
        )
        self.tools = None
        self.agent = None

    async def initialize(self):
        if self.agent is not None:
            return  # Already initialized
        self.tools = await initize_mcp()
        system_prompt = (
            "You are an Attendance and Staff Management Assistant. "
            "You have access to MCP tools to fetch staff details, advanced attendance records, and logs. "
            "Always use 'get_current_time' if the user asks about 'today' or 'yesterday' to establish the correct context. "
            "Your responses should be clear, concise, and heavily based on the output of your tools."
        )
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=system_prompt,
        )
    async def invoke(self, query: str, chat_history: list = None):
        import asyncio
        from langchain_core.messages import HumanMessage, AIMessage
        
        if chat_history is None:
            chat_history = []
            
        messages = []
        for msg in chat_history:
            if isinstance(msg, dict):
                role = msg.get("role", msg.get("type", "user")).lower()
                content = msg.get("content", "")
                if role in ["user", "humanmessage", "human"]:
                    messages.append(HumanMessage(content=content))
                elif role in ["assistant", "aimessage", "ai"]:
                    messages.append(AIMessage(content=content))
                else:
                    messages.append(HumanMessage(content=content))
            else:
                messages.append(msg)
                
        messages.append(HumanMessage(content=query))

        if getattr(self, "agent", None) is None:
            await self.initialize()

        try:
            return await self.agent.ainvoke({"messages": messages})
        except AttributeError:
            # Fallback if agent is synchronous
            return self.agent.invoke({"messages": messages})
if __name__ == "__main__":
    async def test_agent():
        print("Initializing AttendanceAgent...")
        agent = AttendanceAgent()
        await agent.initialize()
        
        chat_history = []
        print("\n=== AttendanceAgent Interactive Test ===")
        print("Type 'exit' or 'quit' to exit.\n")
        
        while True:
            try:
                query = input("User: ").strip()
            except EOFError:
                break
                
            if not query or query.lower() in ["exit", "quit"]:
                print("Exiting test...")
                break
                
            print("Invoking agent...")
            response = await agent.invoke(query=query, chat_history=chat_history)
            
            # The agent responds with the full message history (if it's a LangGraph agent)
            # We can just naturally use that as the chat_history for the next turn.
            if isinstance(response, dict) and "messages" in response:
                chat_history = response["messages"]
                content = chat_history[-1].content
            elif hasattr(response, "content"):
                content = response.content
                chat_history.append({"role": "user", "content": query})
                chat_history.append({"role": "assistant", "content": content})
            else:
                content = str(response)
                chat_history.append({"role": "user", "content": query})
                chat_history.append({"role": "assistant", "content": content})
                
            print(f"Agent: {content}\n")

    asyncio.run(test_agent())