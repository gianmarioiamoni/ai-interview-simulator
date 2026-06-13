# services/interview_scoring/interview_scoring_engine.py

from typing import List
from domain.contracts.question.question import Question
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.user.role import RoleType, ROLE_WEIGHTS
from services.interview_scoring.scoring_result import ScoringResult
from app.ui.presenters.helpers.dimension_ranking import DimensionRanking
from infrastructure.config.evaluation import (
    LEVEL_POOR_THRESHOLD,
    LEVEL_AVERAGE_THRESHOLD,
    LEVEL_STRONG_THRESHOLD,
    HIRING_PROBABILITY_WEAKEST_LOW,
    HIRING_PROBABILITY_WEAKEST_HIGH,
    HIRING_PROBABILITY_WEAKEST_LOW_PENALTY,
    HIRING_PROBABILITY_WEAKEST_HIGH_BONUS,
)

from .components.dimension_scorer import DimensionScorer
from .components.gating_policy import GatingPolicy
from .components.percentile_calculator import PercentileCalculator
from .components.confidence_calculator import ConfidenceCalculator


class InterviewScoringEngine:

    def __init__(self):
        self._dimension_scorer = DimensionScorer()
        self._gating_policy = GatingPolicy()
        self._percentile_calculator = PercentileCalculator()
        self._confidence_calculator = ConfidenceCalculator()

    # ---------------------------------------------------------

    def compute(
        self,
        questions: List[Question],
        evaluations: List[QuestionEvaluation],
        role: RoleType,
    ) -> ScoringResult:

        dimension_scores = self._dimension_scorer.compute(questions, evaluations)

        weighted_breakdown = {
            dim: round(score * ROLE_WEIGHTS[role].get(dim, 0.0), 2)
            for dim, score in dimension_scores.items()
        }

        overall_score = round(sum(weighted_breakdown.values()), 1)

        gating_triggered, gating_reason = self._gating_policy.apply(
            dimension_scores,
            role,
        )

        weakest = min(
            (score for score in dimension_scores.values() if score is not None),
            default=None,
        )

        hiring_probability = (
            0.0 if gating_triggered else self._compute_hiring_probability(overall_score, weakest)
        )

        percentile = self._percentile_calculator.compute(overall_score, role)

        confidence = self._confidence_calculator.compute(evaluations)

        level = self._compute_level(overall_score)

        return ScoringResult(
            dimension_scores=dimension_scores,
            weighted_breakdown=weighted_breakdown,
            overall_score=overall_score,
            level=level,
            gating_triggered=gating_triggered,
            gating_reason=gating_reason,
            hiring_probability=hiring_probability,
            percentile=percentile,
            confidence=confidence,
        )

    # ---------------------------------------------------------

    def _compute_level(self, score: float):

        if score < LEVEL_POOR_THRESHOLD:
            return InterviewLevel.POOR
        elif score < LEVEL_AVERAGE_THRESHOLD:
            return InterviewLevel.AVERAGE
        elif score < LEVEL_STRONG_THRESHOLD:
            return InterviewLevel.STRONG
        return InterviewLevel.EXCELLENT

    def _compute_hiring_probability(self, score: float, weakest: float | None):

        base = score

        if weakest is not None:
            if weakest < HIRING_PROBABILITY_WEAKEST_LOW:
                base -= HIRING_PROBABILITY_WEAKEST_LOW_PENALTY
            elif weakest > HIRING_PROBABILITY_WEAKEST_HIGH:
                base += HIRING_PROBABILITY_WEAKEST_HIGH_BONUS

        return max(0.0, min(100.0, round(base, 1)))
