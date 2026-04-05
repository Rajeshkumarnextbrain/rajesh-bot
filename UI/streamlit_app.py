import json
import uuid
from typing import Generator, Dict, Any

import requests
import streamlit as st

# Configuration
DEFAULT_API_URL = "http://127.0.0.1:7000/api/chat"
THEME_COLOR = "#3B82F6" # Modern Blue

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Outfit:wght@400;600;800&display=swap');

        :root {
            --primary-gradient: linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%);
            --glass-bg: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
        }

        /* Overall Font & Background */
        body {
            font-family: 'Inter', sans-serif;
        }
        
        .main-header {
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3rem !important;
            margin-bottom: 0.5rem;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.95);
            border-right: 1px solid var(--glass-border);
        }

        /* Chat Message Styling */
        .stChatMessage {
            background-color: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            backdrop-filter: blur(10px);
        }

        /* Custom Card for Suggested Queries */
        .suggestion-card {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            padding: 10px 15px;
            margin: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
            font-size: 0.9rem;
            display: inline-block;
        }
        .suggestion-card:hover {
            background: rgba(59, 130, 246, 0.2);
            border-color: #3B82F6;
            transform: translateY(-2px);
        }

        /* Hide Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

def stream_response(
    api_url: str, query: str, history: list[Dict[str, Any]], session_id: str
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream chunks from the chat API, yielding parsed JSON payloads.
    """
    payload = {"query": query, "history": history, "session_id": session_id}
    with requests.post(api_url, json=payload, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        for raw_line in resp.iter_lines(decode_unicode=True):
            if not raw_line or not raw_line.strip():
                continue
            try:
                yield json.loads(raw_line)
            except json.JSONDecodeError:
                continue

def ensure_state():
    if "history" not in st.session_state:
        st.session_state.history = []
    if "api_url" not in st.session_state:
        st.session_state.api_url = DEFAULT_API_URL
    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid.uuid4().hex
    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None

def main():
    st.set_page_config(
        page_title="Analytical Assistant | VisionFacts",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    inject_custom_css()
    ensure_state()

    # --- Sidebar ---
    with st.sidebar:
        st.markdown('<p style="font-family:Outfit; font-weight:800; font-size:1.5rem; margin-top:-2rem;">VisionFacts AI</p>', unsafe_allow_html=True)
        st.divider()
        
        with st.expander("⚙️ Server Settings", expanded=False):
            api_url_input = st.text_input("Chat endpoint", value=st.session_state.api_url)
            st.session_state.api_url = api_url_input.strip() or DEFAULT_API_URL
            st.caption("Target: `agents/event_summary_agent.py`")
        
        st.divider()
        st.subheader("Session Control")
        st.text_input("Session ID", value=st.session_state.session_id, disabled=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("New Session", use_container_width=True):
                st.session_state.session_id = uuid.uuid4().hex
                st.session_state.history = []
                st.rerun()
        with col2:
            if st.button("Clear History", use_container_width=True):
                st.session_state.history = []
                st.rerun()

        st.spacer = st.empty()
        for _ in range(10): st.sidebar.write("")
        st.info("System Ready | Connected to MCP Server via SSE")

    # --- Header ---
    st.markdown('<p class="main-header">Event Summary Agent</p>', unsafe_allow_html=True)
    st.markdown("""
        <p style="font-size:1.2rem; color: #94A3B8; margin-top:-1rem;">
            Real-time analytical insights for events and traffic logs. 
            Powered by <b>Model Context Protocol</b>.
        </p>
    """, unsafe_allow_html=True)

    # --- Chat Display ---
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.history:
            st.markdown("""
                <div style="text-align: center; padding: 40px; border: 1px dashed var(--glass-border); border-radius: 12px; opacity: 0.6;">
                    <h3>Welcome! Ready to analyze.</h3>
                    <p>Ask about today's events, vehicle counts, or crowd density.</p>
                </div>
            """, unsafe_allow_html=True)
        
        for entry in st.session_state.history:
            role = "user" if entry["type"] == "HumanMessage" else "assistant"
            # Special handling for ToolMessages: Render images if present
            if entry["type"] == "ToolMessage":
                content = entry["content"].strip()
                if content:
                    try:
                        # Attempt to parse as JSON to find image data
                        data = json.loads(content)
                        if "image" in data and isinstance(data["image"], str) and data["image"].startswith("data:image"):
                            with st.chat_message("assistant"):
                                st.image(data["image"], caption="Generated Heatmap", use_container_width=True)
                                # st.divider()
                    except:
                        pass # Not a JSON image response, skip rendering technical output
                continue

            # Hide empty thought messages from the UI
            if not entry["content"].strip():
                continue

            with st.chat_message(role):
                st.markdown(entry["content"])
                if entry["tool_calls"]:
                    with st.expander("🛠️ Analytical Steps", expanded=False):
                        for tc in entry["tool_calls"]:
                            st.code(f"Tool: {tc.get('name')} | Args: {json.dumps(tc.get('args'))}", language="json")

    # --- Suggested Queries ---
    if not st.session_state.history:
        suggestions = [
            "What is the total event count for today?",
            "Show me the vehicle line crossing entries for today.",
            "Are there any crowd density alerts (Crowd III/IV)?",
            "Give me a summary of Walk In/Out for all devices."
        ]
        st.markdown("##### Suggested Queries")
        cols = st.columns(len(suggestions))
        for i, suggestion in enumerate(suggestions):
            if cols[i].button(suggestion, use_container_width=True):
                st.session_state.pending_query = suggestion
                st.rerun()

    # --- Chat Input ---
    prompt = st.chat_input("Ask about security events or traffic logs...")
    
    # Handle both normal input and suggested query clicks
    user_query = prompt or st.session_state.pending_query
    
    if user_query:
        st.session_state.pending_query = None # Clear it
        
        # Add human message to history
        st.session_state.history.append({"content": user_query, "type": "HumanMessage", "tool_calls": []})
        
        # Display human message immediately
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_query)

        # Handle Streamed Assistant Response
        with chat_container:
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                status_placeholder = st.status("🔍 Thinking & Analyzing...", expanded=True)
                
                final_content = ""
                final_tool_calls = []

                try:
                    for chunk in stream_response(
                        st.session_state.api_url,
                        user_query,
                        st.session_state.history[:-1], # Don't send the one we just added yet
                        st.session_state.session_id,
                    ):
                        content = chunk.get("content", "")
                        tool_calls = chunk.get("tool_calls", [])
                        tool_call_id = chunk.get("tool_call_id")
                        msg_type = chunk.get("type", "")

                        # Append every message received from the agent to the history
                        # (AI with tool_calls, ToolMessage result, and final AI response)
                        st.session_state.history.append({
                            "content": content,
                            "type": msg_type,
                            "tool_calls": tool_calls,
                            "tool_call_id": tool_call_id
                        })

                        if tool_calls:
                            for tc in tool_calls:
                                status_placeholder.write(f"Calling: `{tc.get('name')}`")

                        if content and msg_type == "AIMessage":
                            final_content = content
                            response_placeholder.markdown(final_content)
                    
                    status_placeholder.update(label="✅ Analysis Complete", state="complete", expanded=False)
                    
                except requests.RequestException as exc:
                    st.error(f"Error: Could not reach the agent at {st.session_state.api_url}. Is the agent running?")
                    return

                if not final_content and not any(m["type"] == "AIMessage" for m in st.session_state.history[-3:]):
                    st.warning("The agent returned an empty response.")
        
        st.rerun()

if __name__ == "__main__":
    main()
