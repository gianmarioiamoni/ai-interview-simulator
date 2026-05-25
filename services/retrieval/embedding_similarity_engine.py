# services/retrieval/embedding_similarity_engine.py

import numpy as np

from services.retrieval.contracts import EmbeddingRecord
from services.embedding.embedding_model_provider import EmbeddingModelProvider


class EmbeddingSimilarityEngine:

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self) -> None:

        self._model = EmbeddingModelProvider.get_model()

    # =====================================================
    # PUBLIC
    # =====================================================

    def rank(
        self,
        query: str,
        records: list[EmbeddingRecord],
    ) -> list[
        tuple[
            EmbeddingRecord,
            float,
        ]
    ]:

        query_embedding = self._model.encode(
            query,
            convert_to_numpy=True,
        )

        scored: list[
            tuple[
                EmbeddingRecord,
                float,
            ]
        ] = []

        for record in records:

            similarity = self._cosine_similarity(
                query_embedding,
                np.array(record.embedding),
            )

            scored.append(
                (
                    record,
                    round(
                        float(similarity),
                        4,
                    ),
                )
            )

        scored.sort(
            key=lambda item: (item[1]),
            reverse=True,
        )

        return scored

    # =====================================================
    # INTERNALS
    # =====================================================

    def _cosine_similarity(
        self,
        a: np.ndarray,
        b: np.ndarray,
    ) -> float:

        return np.dot(
            a,
            b,
        ) / (np.linalg.norm(a) * np.linalg.norm(b))
