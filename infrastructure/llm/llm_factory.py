# infrastructure/llm/llm_factory.py

from langchain_core.language_models import LLM
from langchain_openai import ChatOpenAI

from infrastructure.config.settings import settings


def get_raw_llm() -> LLM:
    return ChatOpenAI(
        model=settings.chat_model,
        temperature=settings.chat_temperature,
        api_key=settings.openai_api_key,
    )
