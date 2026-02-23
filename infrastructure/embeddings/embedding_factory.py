# infrastructure/embeddings/embedding_factory.py

# EmbeddingFactory
#
# Responsibility:
# Creates and configures embedding model instances.
# Centralizes provider selection and configuration.

from langchain_openai import OpenAIEmbeddings

from infrastructure.config.settings import settings


def get_embedding_model() -> OpenAIEmbeddings:
    """
    Factory function to create an embedding model instance.
    
    Returns:
        OpenAIEmbeddings: Configured embedding model
    """
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )
