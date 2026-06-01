# services/question_corpus/repositories/retrieval_embedding_repository.py


class RetrievalEmbeddingRepository:

    # =====================================================
    # CLASS STATE
    # =====================================================

    _embeddings: dict[str, list[float]] = {}

    # =====================================================
    # PUBLIC
    # =====================================================

    @classmethod
    def store(
        cls,
        document_id: str,
        embedding: list[float],
    ) -> None:

        cls._embeddings[document_id] = embedding

    @classmethod
    def get(
        cls,
        document_id: str,
    ) -> list[float] | None:

        return cls._embeddings.get(
            document_id,
        )
