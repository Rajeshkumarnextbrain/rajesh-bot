import asyncio
import os
from dotenv import load_dotenv

from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage, AIMessage

from agents import attendance_agent, dashboard_agent

load_dotenv()

primary_model_name = os.getenv("PRIMARY_MODEL", "gpt-5.4-nano-2026-03-17")

MANAGER_SYSTEM_PROMPT = """
You are a CCTV Video Analytics Assistant responsible for answering user queries by intelligently coordinating multiple specialized sub-agents.

## 🎯 Your Role
You act as the central manager that:
- Understands the user's intent
- Decides which sub-agent(s) to use
- Delegates tasks using the `task` tool
- Combines results into a clear, concise, and structured final response

## 🧠 Available Sub-Agents
- attendance_agent → handles staff attendance, logs, and personnel-related queries
- dashboard_agent → handles security analytics, traffic data, event counts, and line crossings

## ⚙️ Delegation Rules
- Use `attendance_agent` for:
  - attendance summaries
  - staff presence / absence
  - check-in / check-out logs
  - staff anomalies

- Use `dashboard_agent` for:
  - security events
  - traffic analytics
  - line crossings
  - crowd / vehicle insights
  - incident summaries

- If the query requires BOTH (e.g., "today summary"):
  → delegate to BOTH agents in parallel

## 🔄 Execution Strategy
- Always delegate using `task`
- Prefer parallel delegation when multiple domains are involved
- Do NOT answer from your own knowledge if tools are needed
- Wait for sub-agent results before responding

## 🧾 Response Guidelines
- Combine outputs from sub-agents into ONE final answer
- Structure responses clearly using sections when applicable:

Example:
- Attendance Summary
- Security/Traffic Summary
- Notable Events

- Keep answers:
  - concise
  - factual
  - based only on retrieved data

## ⚠️ Handling Missing Data
- If a sub-agent cannot provide data:
  → clearly state: "No data available for this section"

## 📅 Time Awareness
- Interpret terms like "today", "yesterday", "now"
- Ensure sub-agents use correct time context

## 🚫 Do NOT
- Expose internal tool names
- Mention sub-agents explicitly in final answer
- Include reasoning or intermediate steps

## ✅ Final Goal
Provide a clean, professional CCTV analytics summary that helps users quickly understand:
- what happened
- when it happened
- any anomalies or important insights
"""
subagents = [
    {
        "name": "attendance_agent",
        "description": "Attendance logs and staff details.",
        "runnable": attendance_agent,
    },
    {
        "name": "dashboard_agent",
        "description": "Security analytics, counts, and line crossings.",
        "runnable": dashboard_agent,
    },
]


agent = create_deep_agent(
    model=f"openai:{primary_model_name}",
    subagents=subagents,
    system_prompt=MANAGER_SYSTEM_PROMPT,
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
        final_printed = False
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
                    elif not final_printed:
                        content = msg.content
                        # Case 1: string
                        if isinstance(content, str) and content.strip():
                            final_response = content
                            final_printed = True
                        # Case 2: list
                        elif isinstance(content, list):
                            text_parts = [
                                item.get("text", "")
                                for item in content
                                if isinstance(item, dict)
                                and item.get("type") == "text"
                            ]
                            final_response = "".join(text_parts).strip()
                            if final_response:
                                final_printed = True

        # ✅ Print final answer
        if final_response:
            print("===="*10)
            print("\n🤖 Assistant:\n")
            print(final_response)
            # ✅ Save AI response
            chat_history.append(AIMessage(content=final_response))


if __name__ == "__main__":
    asyncio.run(main())