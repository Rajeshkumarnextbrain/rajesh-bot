import os
import asyncio
from dotenv import load_dotenv
import yaml

from langchain_mcp_adapters.client import MultiServerMCPClient
from utils.model_utils import get_chat_model
from langchain.agents import create_agent


load_dotenv()

with open("assets/system_prompts.yaml", "r", encoding="utf-8") as f:
    prompts = yaml.safe_load(f)


async def initize_mcp():
    mcp_client = MultiServerMCPClient(
        {
            'attendance':{
                "transport": "streamable_http",
                "url": os.getenv("ATTENDANCE_MCP_URL", "http://localhost:8000/mcp"),
                "timeout": 120.0,
            }
        }
    )

    # Retry logic for Docker service startup
    for attempt in range(6): # 6 attempts = ~15 seconds
        try:
            print(f"Attempting to connect to MCP server... (Attempt {attempt+1}/6)")
            tools = await mcp_client.get_tools()
            print("Successfully connected to MCP server.")
            return tools
        except Exception as e:
            if attempt == 5:
                print(f"Failed to connect to MCP server after several attempts: {e}")
                raise e
            print(f"MCP connection failed, retrying in 3s... ({e})")
            await asyncio.sleep(3)

    return []

all_tools = asyncio.run(initize_mcp())

primary_model_name = os.getenv("PRIMARY_MODEL", "gpt-5.4-nano-2026-03-17")
temperature = os.getenv("TEMPERATURE", 0.5)
primary_model = get_chat_model(
    model_name=primary_model_name,
    temperature=float(temperature),
)
"""

Attedance Agent

"""
attendance_tools = [tool for tool in all_tools if tool.name in ["get_staffs", "get_attendances_advanced", "get_attendance_logs","get_current_time"]]
attendance_agent = create_agent(
    model=primary_model,
    tools=attendance_tools,
    system_prompt=prompts.get("attendance_agent", "")
)

"""
Dashboard Agent
"""
dashboard_tools = [tool for tool in all_tools if tool.name in ['get_camera_list', 'get_detailed_events', 'get_event_types','get_current_time','get_vehicle_line_crossing_counts','get_line_crossing_counts','get_crowd_counts','get_vehicle_counts','get_event_counts']]
dashboard_agent = create_agent(
    model=primary_model,
    tools=dashboard_tools,
    system_prompt=prompts.get("dashboard_agent", "")
)


"""
output formatter agent

"""
output_formatter_agent = create_agent(
    model=primary_model,
    system_prompt=prompts.get("output_formatter_agent", "")
)