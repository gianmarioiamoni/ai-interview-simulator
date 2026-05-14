# services/question_intelligence/quality/diversity_analyzer.py

from typing import List

from domain.contracts.question.question import (
    Question,
    QuestionDifficulty,
)

from services.question_intelligence.quality.contracts.diversity_report import (
    DiversityReport,
)


class DiversityAnalyzer:

    def analyze(
        self,
        questions: List[Question],
    ) -> DiversityReport:

        if not questions:
            return DiversityReport(
                diversity_score=0.0,
            )

        difficulties = {
            QuestionDifficulty.EASY: 0,
            QuestionDifficulty.MEDIUM: 0,
            QuestionDifficulty.HARD: 0,
        }

        for q in questions:
            difficulties[q.difficulty] += 1

        used_buckets = sum(1 for count in difficulties.values() if count > 0)

        diversity_score = used_buckets / len(difficulties)

        return DiversityReport(
            diversity_score=diversity_score,
        )
