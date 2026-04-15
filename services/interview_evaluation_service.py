# services/interview_evaluation_service.py

from typing import List, Dict, Optional
import logging
import json

from app.ports.llm_port import LLMPort

from domain.contracts.interview.interview_evaluation import InterviewEvaluation
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.shared.performance_dimension import PerformanceDimension
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.feedback.confidence import Confidence
from domain.contracts.question.question import Question
from domain.contracts.user.role import RoleType, ROLE_DISTRIBUTION, ALLOWED_DIMENSIONS
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType
from domain.contracts.shared.performance_dimension_labels import DIMENSION_LABELS

from services.interview_scoring.interview_scoring_engine import InterviewScoringEngine
from services.interview_scoring.decision_explainer import DecisionExplainer

logger = logging.getLogger(__name__)


class InterviewEvaluationService:

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm
        self._scoring_engine = InterviewScoringEngine()
        self._explainer = DecisionExplainer()

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------

    def evaluate(
        self,
        per_question_evaluations: List[QuestionEvaluation],
        questions: List[Question],
        interview_type: InterviewType,
        role: RoleType,
    ) -> InterviewEvaluation:

        if not per_question_evaluations:
            raise ValueError("Cannot evaluate interview without question evaluations")

        scoring = self._scoring_engine.compute(
            questions=questions,
            evaluations=per_question_evaluations,
            role=role,
        )

        logger.info(f"SCORING DEBUG: {scoring}")

        dimension_scores: Dict[PerformanceDimensionType, Optional[float]] = (
            scoring.dimension_scores
        )

        weighted_breakdown = scoring.weighted_breakdown
        overall_score = scoring.overall_score

        gating_triggered = scoring.gating_triggered
        gating_reason = scoring.gating_reason
        hiring_probability = self._compute_hiring_probability(overall_score)

        # ---------------------------------------------------------
        # DECISION EXPLANATION
        # ---------------------------------------------------------

        decision_reasons = self._explainer.explain(
            overall_score=overall_score,
            hire_decision=scoring.hire_decision.value,
            dimension_scores=dimension_scores,
            gating_triggered=gating_triggered,
            gating_reason=gating_reason,
        )

        # ---------------------------------------------------------
        # PERCENTILE
        # ---------------------------------------------------------

        percentile = scoring.percentile

        dist_params = ROLE_DISTRIBUTION[role]
        percentile_explanation = (
            f"Percentile computed analytically using role-specific "
            f"normal distribution (μ={dist_params['mean']}, σ={dist_params['std']})."
        )

        # ---------------------------------------------------------
        # CONFIDENCE
        # ---------------------------------------------------------

        confidence = Confidence(
            base=scoring.confidence,
            final=scoring.confidence,
        )

        # ---------------------------------------------------------
        # EXECUTIVE SUMMARY (SAFE)
        # ---------------------------------------------------------

        executive_summary = self._generate_executive_summary(
            overall_score,
            dimension_scores,
        )

        # ---------------------------------------------------------
        # NARRATIVE
        # ---------------------------------------------------------

        narrative = self._generate_narrative(
            per_question_evaluations,
            dimension_scores,
            interview_type,
            role,
        )

        # ---------------------------------------------------------
        # PERFORMANCE DIMENSIONS
        # ---------------------------------------------------------

        performance_dimensions = []

        for dim, score in dimension_scores.items():

            label = DIMENSION_LABELS.get(dim, dim.value)

            dimension_justification = narrative.get("dimension_justifications", {})

            justification = dimension_justification.get(
                label,
                "Justification unavailable.",
            )

            performance_dimensions.append(
                PerformanceDimension(
                    name=label,
                    score=score,
                    justification=justification,
                )
            )

        # ---------------------------------------------------------
        # MISSING SIGNAL → IMPROVEMENTS
        # ---------------------------------------------------------

        missing_dims = [
            DIMENSION_LABELS.get(dim, dim.value)
            for dim, score in dimension_scores.items()
            if score is None
        ]

        improvement_suggestions = narrative["improvement_suggestions"] or []

        if missing_dims:
            improvement_suggestions += [
                f"{dim} was not assessed → consider practicing this area."
                for dim in missing_dims
            ]

        # ---------------------------------------------------------
        # FINAL OBJECT
        # ---------------------------------------------------------

        return InterviewEvaluation(
            overall_score=overall_score,
            executive_summary=executive_summary,
            performance_dimensions=performance_dimensions,
            dimension_scores=dimension_scores,
            level=scoring.level,
            hire_decision=scoring.hire_decision,
            decision_reasons=decision_reasons,
            hiring_probability=hiring_probability,
            percentile_rank=percentile,
            percentile_explanation=percentile_explanation,
            gating_triggered=gating_triggered,
            gating_reason=gating_reason,
            weighted_breakdown=weighted_breakdown,
            per_question_assessment=per_question_evaluations,
            improvement_suggestions=improvement_suggestions,
            confidence=confidence,
        )

    # ---------------------------------------------------------
    # EXECUTIVE SUMMARY (SAFE VERSION)
    # ---------------------------------------------------------

    def _generate_executive_summary(
        self,
        overall_score: float,
        dimension_scores: Dict[PerformanceDimensionType, Optional[float]],
    ) -> str:

        valid_scores = [s for s in dimension_scores.values() if s is not None]

        if not valid_scores:
            return "Insufficient data to evaluate candidate."

        max_score = max(valid_scores)
        min_score = min(valid_scores)
        spread = max_score - min_score

        if overall_score >= 80:
            base = "The candidate demonstrated strong overall technical performance."
        elif overall_score >= 65:
            base = "The candidate demonstrated solid performance with room for improvement."
        elif overall_score >= 50:
            base = (
                "The candidate demonstrated mixed performance across evaluated areas."
            )
        else:
            base = (
                "The candidate demonstrated significant gaps in key competency areas."
            )

        if spread > 60:
            stability = "Performance was highly inconsistent across dimensions."
        elif spread > 30:
            stability = "Some variability across dimensions was observed."
        else:
            stability = "Performance was relatively consistent across areas."

        return f"{base} {stability}"

    # ---------------------------------------------------------
    # NARRATIVE
    # ---------------------------------------------------------

    def _generate_narrative(
        self,
        evaluations: List[QuestionEvaluation],
        dimension_scores: Dict[PerformanceDimensionType, Optional[float]],
        interview_type: InterviewType,
        role: RoleType,
    ) -> Dict:

        readable_dimension_scores = {
            DIMENSION_LABELS.get(dim, dim.value): (
                score if score is not None else "NOT_EVALUATED"
            )
            for dim, score in dimension_scores.items()
        }

        prompt = f"""
You are a senior technical interviewer.

Role: {role.value}
Interview type: {interview_type.value}

Here are evaluated answers:
{[e.model_dump() for e in evaluations]}

Dimension scores:
{readable_dimension_scores}

Provide:

1. Justification for each dimension
2. 3 improvement suggestions

Return JSON.
"""

        response = self._llm.invoke(prompt)

        try:
            parsed = self._extract_json(response.content)

            if "dimension_justifications" not in parsed:
                parsed["dimension_justifications"] = {}
            if "improvement_suggestions" not in parsed:
                parsed["improvement_suggestions"] = []

            return parsed
        except Exception:
            logger.warning("narrative_json_parsing_failed")

            return {
                "dimension_justifications": {
                    name: "Justification unavailable."
                    for name in DIMENSION_LABELS.values()
                },
                "improvement_suggestions": [],
            }

    # ---------------------------------------------------------

    def _extract_json(self, text: str) -> Dict:
        try:
            return json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            return json.loads(text[start : end + 1])
