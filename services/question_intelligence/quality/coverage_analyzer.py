# services/question_intelligence/quality/coverage_analyzer.py

from collections import Counter
from typing import List

from domain.contracts.question.question import Question

from services.question_intelligence.quality.contracts.coverage_report import (
    CoverageReport,
)


class CoverageAnalyzer:

    def analyze(
        self,
        questions: List[Question],
    ) -> CoverageReport:

        if not questions:
            return CoverageReport(
                area_coverage_score=0.0,
                difficulty_balance_score=0.0,
            )

        # -------------------------------------------------
        # AREA COVERAGE
        # -------------------------------------------------

        areas = [q.area for q in questions]

        unique_areas = len(set(areas))

        area_coverage_score = unique_areas / max(len(areas), 1)

        # -------------------------------------------------
        # DIFFICULTY BALANCE
        # -------------------------------------------------

        difficulties = [q.difficulty for q in questions]

        counts = Counter(difficulties)

        expected = len(questions) / max(len(counts), 1)

        imbalance = sum(abs(count - expected) for count in counts.values())

        difficulty_balance_score = max(
            0.0,
            1.0 - (imbalance / len(questions)),
        )

        return CoverageReport(
            area_coverage_score=area_coverage_score,
            difficulty_balance_score=difficulty_balance_score,
        )
