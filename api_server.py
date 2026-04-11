import os
import asyncio
import json
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.messages import HumanMessage, AIMessage

# Import the initialized agent and helper constants from main.py
from main import agent, TOOL_MESSAGES

load_dotenv()

# -----------------------------
# 🌐 FASTAPI IMPLEMENTATION
# -----------------------------
app = FastAPI(title="VisionFacts Manager API")

class MessageItem(BaseModel):
    model_config = ConfigDict(extra='allow')
    role: str # 'user' or 'assistant'
    content: str

# -----------------------------
# 📦 SESSION MANAGEMENT
# -----------------------------
# Dictionary to store chat history per session_id
# Format: { session_id: [HumanMessage, AIMessage, ...] }
sessions: Dict[str, List[Union[HumanMessage, AIMessage]]] = {}

class ChatRequest(BaseModel):
    query: str
    session_id: str = Field(..., description="Unique ID for the chat session")

async def run_agent_api_stream(query: str, session_id: str):
    """
    Asynchronous generator that yields tool progress and updates,
    while also updating the server-side session history.
    """
    # Get or initialize history for this session
    if session_id not in sessions:
        sessions[session_id] = []
    
    chat_history = sessions[session_id]
    
    seen_tasks = set()
    seen_tools = set()
    final_printed = False
    full_final_answer = ""

    messages = {"messages": chat_history + [HumanMessage(content=query)]}

    async for chunk in agent.astream(
        messages,
        stream_mode="updates",
        subgraphs=True,
        version="v2"
    ):
        data = chunk.get("data", {})
        for key, value in data.items():
            if 'before_agent' in key:
                yield json.dumps({"type": "status", "content": "🤖 Thinking..."}) + "\n"
            
            elif 'model' == key:
                msg = value.get('messages', [])[0]
                
                if getattr(msg, 'tool_calls', None):
                    for tool in msg.tool_calls:
                        if tool["name"] == "task":
                            description = tool['args'].get('description')
                            if description not in seen_tasks:
                                seen_tasks.add(description)
                                yield json.dumps({"type": "task", "content": f"🧠 Understanding task: {description}"}) + "\n"
                        else:
                            tool_name = tool["name"]
                            if tool_name not in seen_tools:
                                seen_tools.add(tool_name)
                                tool_msg = TOOL_MESSAGES.get(tool_name, "🔄 Processing...")
                                yield json.dumps({"type": "tool", "content": tool_msg}) + "\n"
                
                elif not final_printed:
                    content = msg.content
                    final_text = ""
                    if isinstance(content, str) and content.strip():
                        final_text = content
                    elif isinstance(content, list):
                        text_parts = [
                            item.get("text", "")
                            for item in content
                            if isinstance(item, dict) and item.get("type") == "text"
                        ]
                        final_text = "".join(text_parts).strip()
                    
                    if final_text:
                        final_printed = True
                        full_final_answer = final_text
                        yield json.dumps({"type": "answer", "content": final_text}) + "\n"

    # Update session history after completion
    if full_final_answer:
        sessions[session_id].append(HumanMessage(content=query))
        sessions[session_id].append(AIMessage(content=full_final_answer))

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        return StreamingResponse(
            run_agent_api_stream(request.query, request.session_id),
            media_type="text/event-stream"
        )
    except Exception as e:
        print(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# -----------------------------
# 🚀 ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    # Configuration from environment variables
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "9000"))
    
    print(f"VisionFacts Manager API starting on {host}:{port}...")
    uvicorn.run(app, host=host, port=port)
