# services/question_intelligence/quality/question_set_quality_analyzer.py

from typing import List

from domain.contracts.question.question import Question

from services.question_intelligence.quality.similarity_engine import SimilarityEngine
from services.question_intelligence.quality.diversity_analyzer import DiversityAnalyzer
from services.question_intelligence.quality.coverage_analyzer import CoverageAnalyzer
from services.question_intelligence.quality.contracts.question_set_quality_report import QuestionSetQualityReport


class QuestionSetQualityAnalyzer:

    def __init__(self) -> None:

        self._similarity_engine = SimilarityEngine()

        self._diversity_analyzer = DiversityAnalyzer()

        self._coverage_analyzer = CoverageAnalyzer()

    # =====================================================
    # PUBLIC
    # =====================================================

    def analyze(
        self,
        questions: List[Question],
    ) -> QuestionSetQualityReport:

        similarity = self._similarity_engine.compute_metrics(
            questions,
        )

        diversity = self._diversity_analyzer.analyze(
            questions,
        )

        coverage = self._coverage_analyzer.analyze(
            questions,
        )

        return QuestionSetQualityReport(
            similarity=similarity,
            diversity=diversity,
            coverage=coverage,
        )
