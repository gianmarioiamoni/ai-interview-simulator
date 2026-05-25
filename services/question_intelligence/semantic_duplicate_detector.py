# services/question_intelligence/semantic_duplicate_detector.py

from sklearn.metrics.pairwise import cosine_similarity

import numpy as np

from services.embedding.embedding_model_provider import EmbeddingModelProvider


class SemanticDuplicateDetector:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        similarity_threshold: float = 0.88,
    ) -> None:

        self._threshold = similarity_threshold

        self._model = EmbeddingModelProvider.get_model()

    # =====================================================
    # PUBLIC
    # =====================================================

    def find_duplicates(
        self,
        questions: list[str],
    ) -> list[tuple[str, str, float]]:

        if len(questions) < 2:
            return []

        embeddings = self._model.encode(
            questions,
            convert_to_numpy=True,
        )

        duplicates = []

        for i in range(len(questions)):

            for j in range(
                i + 1,
                len(questions),
            ):

                similarity = cosine_similarity(
                    [embeddings[i]],
                    [embeddings[j]],
                )[
                    0
                ][0]

                similarity = float(
                    np.round(
                        similarity,
                        4,
                    )
                )

                if similarity >= self._threshold:

                    duplicates.append(
                        (
                            questions[i],
                            questions[j],
                            similarity,
                        )
                    )

        return duplicates
