import asyncio
import os
import yaml
from dotenv import load_dotenv

from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage, AIMessage
from deepagents.backends.filesystem import FilesystemBackend

from agents import attendance_agent, dashboard_agent, output_formatter_agent

load_dotenv()
backend = FilesystemBackend(root_dir=".", virtual_mode=False)

primary_model_name = os.getenv("PRIMARY_MODEL", "gpt-5.4-nano-2026-03-17")

with open("assets/system_prompts.yaml", "r", encoding="utf-8") as f:
    prompts = yaml.safe_load(f)

MANAGER_SYSTEM_PROMPT = prompts.get("manager_agent", "")

subagents = [
    {
        "name": "attendance_agent",
        "description": "Attendance logs and staff details.",
        "runnable": attendance_agent,
        "backend": backend,
        "skills": ["./skills/attendance/"],
    },
    {
        "name": "dashboard_agent",
        "description": "Security analytics, counts, and line crossings.",
        "runnable": dashboard_agent,
        "backend": backend,
        "skills": ["./skills/dashboard/"],
    },
    {
        "name": "output_formatter_agent",
        "description": "Output formatter and presentation.",
        "runnable": output_formatter_agent,
        "backend": backend,
    },
]


agent = create_deep_agent(
    model=f"openai:{primary_model_name}",
    subagents=subagents,
    system_prompt=MANAGER_SYSTEM_PROMPT,
    backend=backend,
    skills=["./skills/main/"]
)


TOOL_MESSAGES = {
    "get_current_time": "🕒 Getting current system time...",
    "get_attendances_advanced": "📊 Fetching today's attendance records...",
    "get_attendance_logs": "📊 Fetching attendance logs...",
    "get_event_counts": "📈 Analyzing event activity...",
    "get_line_crossing_counts": "🚶 Checking line crossing activity...",
    "get_vehicle_counts": "🚗 Gathering vehicle data...",
    "get_vehicle_line_crossing_counts": "🚘 Checking vehicle movement...",
    "get_crowd_counts": "👥 Analyzing crowd density...",
    'get_staffs': "👥 Analyzing staff details...",
    'get_event_types': "Fetching the event types...",

}

chat_history = []

async def main():
    while True:
        query = input("\n👤 You: ")
        if query.lower() in ["exit", "quit"]:
            break
        # ✅ Reset per turn
        seen_tasks = set()
        seen_tools = set()
        # ✅ Add user message
        chat_history.append(HumanMessage(content=query))
        messages = {
            "messages": chat_history
        }
        final_response = ""
        async for chunk in agent.astream(
            messages,
            stream_mode="updates",
            subgraphs=True,
            version="v2"
        ):
            data = chunk.get("data", {})
            for key, value in data.items():
                if 'before_agent' in key:
                    print("🤖 Thinking...")
                elif 'model' == key:
                    msg = value.get('messages', [])[0]
                    # -----------------------------
                    # 📝 TASK + 🔧 TOOL HANDLING
                    # -----------------------------
                    if msg.tool_calls:
                        for tool in msg.tool_calls:
                            # 📝 TASK (subagent delegation)
                            if tool["name"] == "task":
                                description = tool['args'].get('description')
                                if description not in seen_tasks:
                                    seen_tasks.add(description)
                                    print(f"\n🧠 Understanding task:")
                                    print(f"   → {description}")
                            # 🔧 TOOL (user-friendly)
                            else:
                                tool_name = tool["name"]
                                if tool_name not in seen_tools:
                                    seen_tools.add(tool_name)
                                    print(
                                        TOOL_MESSAGES.get(
                                            tool_name,
                                            "🔄 Processing..."
                                        )
                                    )
                    # -----------------------------
                    # 🧠 FINAL ANSWER
                    # -----------------------------
                    elif getattr(msg, "content", None):
                        content = msg.content
                        # Case 1: string
                        if isinstance(content, str) and content.strip():
                            final_response = content
                        # Case 2: list
                        elif isinstance(content, list):
                            text_parts = [
                                item.get("text", "")
                                for item in content
                                if isinstance(item, dict)
                                and item.get("type") == "text"
                            ]
                            new_text = "".join(text_parts).strip()
                            if new_text:
                                final_response = new_text

        # ✅ Print final answer
        if final_response:
            print("===="*10)
            print("\n🤖 Assistant:\n")
            print(final_response)
            # ✅ Save AI response
            chat_history.append(AIMessage(content=final_response))


if __name__ == "__main__":
    asyncio.run(main())