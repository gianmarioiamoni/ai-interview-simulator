# services/interview_scoring/components/confidence_calculator.py

import statistics
from typing import List
from domain.contracts.question.question_evaluation import QuestionEvaluation
from infrastructure.config.evaluation import (
    FEEDBACK_CONFIDENCE_MIN_QUESTIONS,
    FEEDBACK_CONFIDENCE_LOW_SAMPLE,
)


class ConfidenceCalculator:

    def compute(self, evaluations: List[QuestionEvaluation]) -> float:

        scores = [q.score for q in evaluations]

        if len(scores) < FEEDBACK_CONFIDENCE_MIN_QUESTIONS:
            return FEEDBACK_CONFIDENCE_LOW_SAMPLE

        variance = statistics.pvariance(scores)

        return round(1 / (1 + variance / 1000.0), 2)
