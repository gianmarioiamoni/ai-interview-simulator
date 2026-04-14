# services/interview_scoring/interview_scoring_engine.py

from typing import List, Dict, Optional
import statistics
import math

from domain.contracts.question.question import Question
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType
from domain.contracts.user.role import (
    RoleType,
    ROLE_DISTRIBUTION,
    ALLOWED_DIMENSIONS,
    ROLE_WEIGHTS,
)

from services.interview_scoring.scoring_result import ScoringResult



class InterviewScoringEngine:

    def compute(
        self,
        questions: List[Question],
        evaluations: List[QuestionEvaluation],
        role: RoleType,
    ) -> "ScoringResult":

        dimension_scores = self._compute_dimension_scores(questions, evaluations)

        weighted_breakdown = self._compute_weighted_breakdown(
            dimension_scores,
            role,
        )

        overall_score = round(sum(weighted_breakdown.values()), 1)

        gating_triggered, gating_reason = self._apply_gating_rule(
            dimension_scores,
            role,
        )

        if gating_triggered:
            hiring_probability = 0.0
        else:
            hiring_probability = self._compute_hiring_probability(overall_score)

        percentile = self._compute_percentile(overall_score, role)

        confidence = self._compute_confidence(evaluations)

        level = self._compute_level(overall_score)
        hire_decision = self._compute_hire_decision(overall_score, gating_triggered)

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

    def _compute_level(self, score: float) -> InterviewLevel:

        if score < 50:
            return InterviewLevel.POOR
        elif score < 65:
            return InterviewLevel.AVERAGE
        elif score < 80:
            return InterviewLevel.STRONG
        else:
            return InterviewLevel.EXCELLENT


    def _compute_dimension_scores(
        self,
        questions: List[Question],
        evaluations: List[QuestionEvaluation],
    ) -> Dict[PerformanceDimensionType, float]:

        question_area_map = {q.id: q.area for q in questions}

        AREA_TO_DIMENSION = {
            "technical_background": PerformanceDimensionType.TECHNICAL_DEPTH,
            "technical_technical_knowledge": PerformanceDimensionType.TECHNICAL_DEPTH,
            "technical_database": PerformanceDimensionType.TECHNICAL_DEPTH,
            "technical_coding": PerformanceDimensionType.PROBLEM_SOLVING,
            "technical_case_study": PerformanceDimensionType.SYSTEM_DESIGN,
            "hr_background": PerformanceDimensionType.COMMUNICATION,
            "hr_technical_knowledge": PerformanceDimensionType.TECHNICAL_DEPTH,
            "hr_situational": PerformanceDimensionType.COMMUNICATION,
            "hr_brain_teaser": PerformanceDimensionType.PROBLEM_SOLVING,
            "hr_analytical": PerformanceDimensionType.PROBLEM_SOLVING,
        }

        dimension_map: Dict[PerformanceDimensionType, List[float]] = {}

        for ev in evaluations:
            area = question_area_map.get(ev.question_id)
            if not area:
                continue

            dimension = AREA_TO_DIMENSION.get(area)
            if not dimension:
                continue

            dimension_map.setdefault(dimension, []).append(ev.score)

        result: Dict[str, float] = {}

        for dimension in PerformanceDimensionType:
            scores = dimension_map.get(dimension, [])
            result[dimension] = round(sum(scores) / len(scores), 1) if scores else 0.0

        return result

    # ---------------------------------------------------------

    def _compute_weighted_breakdown(
        self,
        dimension_scores: Dict[str, float],
        role: RoleType,
    ) -> Dict[str, float]:

        weights = ROLE_WEIGHTS[role]

        return {
            dim: round(score * weights.get(dim, 0.0), 2)
            for dim, score in dimension_scores.items()
        }

    # ---------------------------------------------------------

    def _apply_gating_rule(
        self,
        dimension_scores: Dict[str, float],
        role: RoleType,
    ) -> tuple[bool, Optional[str]]:

        critical_dimensions = {
            RoleType.BACKEND_ENGINEER: ["System Design"],
        }

        for dim in critical_dimensions.get(role, []):
            if dimension_scores.get(dim, 0.0) == 0.0:
                return True, f"Critical dimension '{dim}' scored 0.0"

        return False, None

    # ---------------------------------------------------------

    def _compute_hiring_probability(self, score: float) -> float:

        if score < 50:
            return 0.0
        elif score < 60:
            return 30.0
        elif score < 70:
            return 50.0
        elif score < 80:
            return 70.0
        elif score < 90:
            return 85.0
        return 95.0

    # ---------------------------------------------------------

    def _compute_hire_decision(
        self,
        score: float,
        gating_triggered: bool,
    ) -> HireDecision:

        # Hard fail via gating
        if gating_triggered:
            return HireDecision.NO_HIRE

        if score < 55:
            return HireDecision.NO_HIRE
        elif score < 65:
            return HireDecision.LEAN_NO_HIRE
        elif score < 75:
            return HireDecision.LEAN_HIRE
        else:
            return HireDecision.HIRE


    def _compute_percentile(self, score: float, role: RoleType) -> float:

        params = ROLE_DISTRIBUTION[role]
        mean = params["mean"]
        std = params["std"]

        if std <= 0:
            return 50.0

        z = (score - mean) / std
        percentile = 0.5 * (1 + math.erf(z / math.sqrt(2)))

        return round(percentile * 100, 1)

    # ---------------------------------------------------------

    def _compute_confidence(
        self,
        evaluations: List[QuestionEvaluation],
    ) -> float:

        scores = [q.score for q in evaluations]

        if len(scores) < 2:
            return 0.7

        variance = statistics.pvariance(scores)

        confidence_value = 1 / (1 + variance / 1000.0)
        return round(confidence_value, 2)
