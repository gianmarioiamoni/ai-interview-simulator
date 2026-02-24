# infrastructure/llm/llm_factory.py

from langchain_openai import ChatOpenAI
import os


def get_llm():
    # Factory for creating the default LLM instance
    # Central place to configure model, temperature, etc.

    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
