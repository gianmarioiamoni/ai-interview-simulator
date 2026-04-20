# services/interview_scoring/interview_scoring_engine.py

from typing import List
from domain.contracts.question.question import Question
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.user.role import RoleType, ROLE_WEIGHTS

from services.interview_scoring.scoring_result import ScoringResult
from app.ui.presenters.helpers.dimension_ranking import DimensionRanking

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
            dim: round(score * ROLE_WEIGHTS[role].get(dim.value, 0.0), 2)
            for dim, score in dimension_scores.items()
        }

        overall_score = round(sum(weighted_breakdown.values()), 1)

        gating_triggered, gating_reason = self._gating_policy.apply(
            dimension_scores,
            role,
        )

        hiring_probability = (
            0.0 if gating_triggered else self._compute_hiring_probability(overall_score)
        )

        percentile = self._percentile_calculator.compute(overall_score, role)

        confidence = self._confidence_calculator.compute(evaluations)

        level = self._compute_level(overall_score)
        hire_decision = self._compute_hire_decision(
            overall_score, 
            gating_triggered, 
            dimension_scores,
        )

        return ScoringResult(
            dimension_scores=dimension_scores,
            weighted_breakdown=weighted_breakdown,
            overall_score=overall_score,
            level=level,
            hire_decision=hire_decision,
            gating_triggered=gating_triggered,
            gating_reason=gating_reason,
            hiring_probability=hiring_probability,
            percentile=percentile,
            confidence=confidence,
        )

    # ---------------------------------------------------------

    def _compute_hire_decision(
        self, 
        score: float, 
        gating_triggered: bool,
        dimension_scores: dict):

        if gating_triggered:
            return HireDecision.NO_HIRE

        _strongest, weakest = DimensionRanking.compute(dimension_scores)

        # penalty if weakest is low
        if weakest and weakest.score < 65:
            return HireDecision.LEAN_NO_HIRE


        if score < 55:
            return HireDecision.NO_HIRE
        elif score < 65:
            return HireDecision.LEAN_NO_HIRE
        elif score < 75:
            return HireDecision.LEAN_HIRE
        return HireDecision.HIRE

    def _compute_level(self, score: float):

        if score < 50:
            return InterviewLevel.POOR
        elif score < 65:
            return InterviewLevel.AVERAGE
        elif score < 80:
            return InterviewLevel.STRONG
        return InterviewLevel.EXCELLENT

    def _compute_hiring_probability(self, score: float, weakest: float | None):

        base = score

        if weakest is not None:
            if weakest < 70:
                base -= 5
            elif weakest > 90: 
                base += 3
        
        return max(0.0, min(100.0, round(base, 1)))
