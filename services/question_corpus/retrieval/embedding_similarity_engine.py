# services/question_corpus/retrieval/embedding_similarity_engine.py

from langchain_openai import OpenAIEmbeddings


class EmbeddingSimilarityEngine:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._embeddings = OpenAIEmbeddings()

    # =====================================================
    # PUBLIC
    # =====================================================

    def similarity(
        self,
        text_a: str,
        text_b: str,
    ) -> float:

        embedding_a = self._embeddings.embed_query(
            text_a,
        )

        embedding_b = self._embeddings.embed_query(
            text_b,
        )

        return self._cosine_similarity(
            embedding_a,
            embedding_b,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _cosine_similarity(
        self,
        vector_a: list[float],
        vector_b: list[float],
    ) -> float:

        dot_product = sum(a * b for a, b in zip(vector_a, vector_b))

        magnitude_a = sum(a * a for a in vector_a) ** 0.5

        magnitude_b = sum(b * b for b in vector_b) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        
        return dot_product / (magnitude_a * magnitude_b)
