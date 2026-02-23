# services/question_intelligence/embedding_service.py

# EmbeddingService
#
# Responsibility:
# Provides a clean abstraction over embedding generation.
# Delegates model creation to embedding_factory.
# Ensures the rest of the system is independent from provider details.

from typing import List

from infrastructure.embeddings.embedding_factory import get_embedding_model


class EmbeddingService:
    def __init__(self) -> None:
        self._embedding_model = get_embedding_model()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self._embedding_model.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        return self._embedding_model.embed_query(query)
