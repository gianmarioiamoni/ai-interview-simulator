# infrastructure/embeddings/embedding_similarity_engine.py

import math


class EmbeddingSimilarityEngine:

    def similarity(
        self,
        embedding_a: list[float],
        embedding_b: list[float],
    ) -> float:

        dot_product = sum(
            a * b
            for a, b in zip(
                embedding_a,
                embedding_b,
            )
        )

        norm_a = math.sqrt(sum(x * x for x in embedding_a))

        norm_b = math.sqrt(sum(x * x for x in embedding_b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)
