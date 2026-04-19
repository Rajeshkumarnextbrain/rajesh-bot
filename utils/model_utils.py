import os
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

def get_chat_model(model_name: str = None, temperature: float = 0.5):
    """
    Returns the appropriate LangChain chat model based on the model name.
    """
    if model_name is None:
        model_name = os.getenv("PRIMARY_MODEL", "gpt-5.4-nano-2026-03-17")
    
    if "gemini" in model_name.lower():
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )
    else:
        # Default to OpenAI for other models
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_retries=5,
        )
