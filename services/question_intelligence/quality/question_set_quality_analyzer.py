# services/question_intelligence/quality/question_set_quality_analyzer.py

from itertools import combinations
from typing import List

from domain.contracts.question.question import Question

from services.question_intelligence.quality.quality_report import (
    QualityReport,
)


class QuestionSetQualityAnalyzer:

    def analyze(
        self,
        questions: List[Question],
    ) -> QualityReport:

        similarities = []

        for q1, q2 in combinations(questions, 2):

            similarity = self._compute_similarity(
                q1.prompt,
                q2.prompt,
            )

            similarities.append(similarity)

        if not similarities:

            return QualityReport(
                average_similarity=0.0,
                max_similarity=0.0,
                duplicate_pairs=0,
                diversity_score=1.0,
            )

        avg_similarity = sum(similarities) / len(similarities)

        max_similarity = max(similarities)

        duplicate_pairs = len([s for s in similarities if s > 0.85])

        diversity_score = 1.0 - avg_similarity

        return QualityReport(
            average_similarity=avg_similarity,
            max_similarity=max_similarity,
            duplicate_pairs=duplicate_pairs,
            diversity_score=diversity_score,
        )

    # =====================================================
    # SIMILARITY
    # =====================================================

    def _compute_similarity(
        self,
        a: str,
        b: str,
    ) -> float:

        # temporary heuristic
        # future:
        # embeddings cosine similarity

        a_words = set(a.lower().split())
        b_words = set(b.lower().split())

        intersection = len(a_words & b_words)
        union = len(a_words | b_words)

        if union == 0:
            return 0.0

        return intersection / union
