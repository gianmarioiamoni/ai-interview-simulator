# services/question_intelligence/diagnostics/retrieval_diversity_analyzer.py

from typing import List

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.question_intelligence.diagnostics.retrieval_similarity_engine import (
    RetrievalSimilarityEngine,
)

from services.question_intelligence.diagnostics.retrieval_quality_report import (
    RetrievalQualityReport,
)


class RetrievalDiversityAnalyzer:

    def __init__(self) -> None:

        self._similarity_engine = RetrievalSimilarityEngine()

    # =====================================================
    # PUBLIC
    # =====================================================

    def analyze(
        self,
        items: List[QuestionBankItem],
    ) -> RetrievalQualityReport:

        similarities = self._similarity_engine.compute_pairwise_similarity(
            items,
        )

        if not similarities:

            return RetrievalQualityReport(
                retrieved_count=len(items),
                average_similarity=0.0,
                max_similarity=0.0,
                diversity_score=1.0,
                duplicate_risk=0.0,
            )

        avg_similarity = sum(similarities) / len(similarities)

        max_similarity = max(similarities)

        diversity_score = max(0.0, 1.0 - avg_similarity)

        duplicate_risk = max_similarity

        return RetrievalQualityReport(
            retrieved_count=len(items),
            average_similarity=round(avg_similarity, 2),
            max_similarity=round(max_similarity, 2),
            diversity_score=round(diversity_score, 2),
            duplicate_risk=round(duplicate_risk, 2),
        )
