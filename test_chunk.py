import asyncio
from main import agent
from langchain_core.messages import HumanMessage

async def test_stream():
    messages = {"messages": [HumanMessage(content="hi can you give overall summary?")]}
    async for chunk in agent.astream(
        messages,
        stream_mode="updates",
        subgraphs=True,
        version="v2"
    ):
        print("CHUNK NS:", chunk.get('ns', []))
        data = chunk.get("data", {})
        for key, value in data.items():
            if key == "model":
                msg = value.get("messages", [])[0]
                if getattr(msg, "content", None):
                    print("CONTENT:", repr(msg.content)[:100])

if __name__ == "__main__":
    asyncio.run(test_stream())
