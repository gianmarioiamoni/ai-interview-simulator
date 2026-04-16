# services/interview_scoring/components/confidence_calculator.py

import statistics
from typing import List
from domain.contracts.question.question_evaluation import QuestionEvaluation


class ConfidenceCalculator:

    def compute(self, evaluations: List[QuestionEvaluation]) -> float:

        scores = [q.score for q in evaluations]

        if len(scores) < 2:
            return 0.7

        variance = statistics.pvariance(scores)

        return round(1 / (1 + variance / 1000.0), 2)
