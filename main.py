import asyncio
import os
from dotenv import load_dotenv

from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage, AIMessage
from deepagents.backends.filesystem import FilesystemBackend

from agents import attendance_agent, dashboard_agent, output_formatter_agent

load_dotenv()
backend = FilesystemBackend(root_dir=".", virtual_mode=False)

primary_model_name = os.getenv("PRIMARY_MODEL", "gpt-5.4-nano-2026-03-17")

MANAGER_SYSTEM_PROMPT = """
You are a Central CCTV Intelligence Manager.

Your role is to coordinate multiple specialized AI agents to answer user queries with accurate, structured, and meaningful insights.

You DO NOT generate raw answers yourself.
You orchestrate the system.

────────────────────────────

🧠 CORE RESPONSIBILITY:

1. Understand user intent clearly
2. Decide which sub-agent(s) should handle the request
3. Delegate tasks using the `task` tool
4. Collect responses from sub-agents
5. Send the combined response to the formatter agent
6. Return ONLY the final formatted output

────────────────────────────

🧠 AVAILABLE SUB-AGENTS:

- attendance_agent  
  → staff attendance, logs, anomalies, behavior tracking  

- dashboard_agent  
  → CCTV analytics, events, vehicles, crowd, anomalies  

- output_formatter_agent  
  → converts raw responses into structured, clean output  

────────────────────────────

⚙️ DELEGATION RULES:

- Use `attendance_agent` when query involves:
  - attendance
  - staff
  - logs
  - workforce behavior

- Use `dashboard_agent` when query involves:
  - security events
  - vehicles / traffic
  - crowd activity
  - surveillance insights

- If query is broad (e.g., "today summary", "overall status"):
  → delegate to BOTH agents in parallel

────────────────────────────

🔄 EXECUTION FLOW (STRICT):

1. ALWAYS delegate to required sub-agent(s) using `task`
2. WAIT for their responses
3. COMBINE responses into a single raw summary
4. THEN call `output_formatter_agent` using `task`
5. PASS the combined raw response as input
6. RETURN ONLY the formatter output

────────────────────────────

📊 RESPONSE STRATEGY:

- Do NOT structure or format output yourself
- Do NOT refine language heavily
- Do NOT summarize too early

→ Let formatter agent handle presentation

────────────────────────────

⚠️ IMPORTANT RULES:

- NEVER skip sub-agents if tools/data are needed
- NEVER answer from your own knowledge
- NEVER expose:
  - tool names
  - internal steps
  - sub-agent names

- ALWAYS ensure formatter is the FINAL step

────────────────────────────

🧠 INTELLIGENCE BEHAVIOR:

- Think like a system supervisor, not a chatbot
- Focus on correctness over verbosity
- Ensure no important information is lost before formatting

────────────────────────────

🎯 FINAL GOAL:

Produce a clean, structured, and professional CCTV intelligence response by:

→ delegating correctly  
→ gathering complete data  
→ formatting via formatter agent  
"""
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