# services/question_intelligence/quality/similarity_engine.py

from itertools import combinations
from typing import List

from domain.contracts.question.question import Question

from services.question_intelligence.quality.contracts.similarity_metrics import (
    SimilarityMetrics,
)


class SimilarityEngine:

    def compute_metrics(
        self,
        questions: List[Question],
    ) -> SimilarityMetrics:

        similarities: List[float] = []

        duplicate_pairs = 0

        for q1, q2 in combinations(questions, 2):

            similarity = self._compute_similarity(
                q1.prompt,
                q2.prompt,
            )

            similarities.append(similarity)

            if similarity >= 0.9:
                duplicate_pairs += 1

        if not similarities:
            return SimilarityMetrics(
                average_similarity=0.0,
                max_similarity=0.0,
                duplicate_pairs=0,
            )

        return SimilarityMetrics(
            average_similarity=sum(similarities) / len(similarities),
            max_similarity=max(similarities),
            duplicate_pairs=duplicate_pairs,
        )

    # =====================================================
    # INTERNAL
    # =====================================================

    def _compute_similarity(
        self,
        text_a: str,
        text_b: str,
    ) -> float:

        tokens_a = set(text_a.lower().split())
        tokens_b = set(text_b.lower().split())

        if not tokens_a or not tokens_b:
            return 0.0

        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)

        return len(intersection) / len(union)
