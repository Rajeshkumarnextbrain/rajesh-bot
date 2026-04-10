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

    return tools

all_tools = asyncio.run(initize_mcp())

primary_model_name = os.getenv("PRIMARY_MODEL", "gpt-5.4-nano-2026-03-17")
temperature = os.getenv("TEMPERATURE", 0.5)
primary_model = ChatOpenAI(
    model=primary_model_name,
    temperature=temperature,
)
"""

Attedance Agent

"""
attendance_tools = [tool for tool in all_tools if tool.name in ["get_staffs", "get_attendances_advanced", "get_attendance_logs","get_current_time"]]
attendance_agent = create_agent(
    model=primary_model,
    tools=attendance_tools,
    system_prompt=(
            "You are an Attendance and Staff Management Assistant. "
            "You have access to MCP tools to fetch staff details, advanced attendance records, and logs. "
            "Always use 'get_current_time' if the user asks about 'today' or 'yesterday' to establish the correct context. "
            "Your responses should be clear, concise, and heavily based on the output of your tools."
        )
)

"""
Dashboard Agent
"""
dashboard_tools = [tool for tool in all_tools if tool.name in ['get_event_types','get_current_time','get_vehicle_line_crossing_counts','get_line_crossing_counts','get_crowd_counts','get_vehicle_counts','get_event_counts']]
dashboard_agent = create_agent(
    model=primary_model,
    tools=dashboard_tools,
    system_prompt=(
            "You are an expert CCTV analytics assistant for security and traffic monitoring.\n\n"

        "Use tools to retrieve accurate data.\n\n"

        "⚠️ IMPORTANT OUTPUT RULES:\n"
        "- DO NOT return raw JSON\n"
        "- DO NOT dump raw tool outputs\n"
        "- ALWAYS convert data into human-readable summaries\n\n"

        "📊 Format responses like:\n"
        "- Short bullet points\n"
        "- Clear sections\n"
        "- Highlight key numbers and anomalies\n\n"

        "Example sections:\n"
        "- Vehicle Summary\n"
        "- Line Crossing Activity\n"
        "- Notable Events\n\n"

        "Keep responses concise, clear, and readable for operators."
        )
)