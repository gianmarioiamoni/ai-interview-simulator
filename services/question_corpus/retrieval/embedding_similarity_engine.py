# services/question_corpus/retrieval/embedding_similarity_engine.py

from infrastructure.embeddings.embedding_factory import (
    get_embedding_model,
)


class EmbeddingSimilarityEngine:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._embedding_model = get_embedding_model()

    # =====================================================
    # PUBLIC
    # =====================================================

    def similarity(
        self,
        left: str,
        right: str,
    ) -> float:

        embeddings = self._embedding_model.embed_documents(
            [
                left,
                right,
            ]
        )

        return self._cosine_similarity(
            embeddings[0],
            embeddings[1],
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _cosine_similarity(
        self,
        a: list[float],
        b: list[float],
    ) -> float:

        dot_product = sum(
            x * y
            for x, y in zip(
                a,
                b,
            )
        )

        norm_a = sum(x * x for x in a) ** 0.5

        norm_b = sum(y * y for y in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)
