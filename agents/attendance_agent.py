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
                "url": "http://localhost:8000/sse",
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
    def __init__(self,model="gpt-5.4-nano-2026-03-17", temperature=0.5):
        self.tools = initize_mcp()
        self.model = ChatOpenAI(
            model=model,
            temperature=temperature,
        )
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt="",
        )

if __name__ == "__main__":
    asyncio.run(initize_mcp())