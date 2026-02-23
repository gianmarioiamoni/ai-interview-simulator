# infrastructure/llm/llm_factory.py

# LLMFactory
#
# Responsibility:
# Creates and configures LLM instances.
# Centralizes model selection and configuration.

from langchain_openai import ChatOpenAI

from infrastructure.config.settings import settings


def get_llm() -> ChatOpenAI:
    """
    Factory function to create an LLM instance.
    
    Returns:
        ChatOpenAI: Configured LLM instance
    """
    return ChatOpenAI(
        model=settings.model_name,
        openai_api_key=settings.openai_api_key,
        temperature=0.0,
    )
