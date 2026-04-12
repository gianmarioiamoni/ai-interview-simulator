# services/interview_evaluation_service.py

# Interview evaluation service
#
# Enterprise deterministic core version.
#
# Responsibility:
# - deterministic scoring engine
# - deterministic hiring probability
# - deterministic confidence
# - analytical percentile computation (role-aware)
# - gating governance rules
# - LLM only for qualitative justification

from typing import List, Dict
import statistics
import logging
import json
import math

from app.ports.llm_port import LLMPort

from domain.contracts.interview_evaluation import InterviewEvaluation
from domain.contracts.interview_type import InterviewType
from domain.contracts.performance_dimension import PerformanceDimension
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.feedback.feedback.confidence import Confidence
from domain.contracts.question import Question
from domain.contracts.role import RoleType, ROLE_DISTRIBUTION, ALLOWED_DIMENSIONS, ROLE_WEIGHTS


logger = logging.getLogger(__name__)


class InterviewEvaluationService:

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

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

        # 1️⃣ Dimension scoring
        dimension_scores = self._compute_dimension_scores(
            questions,
            per_question_evaluations,
        )

        # 2️⃣ Weighted breakdown
        weighted_breakdown = self._compute_weighted_breakdown(
            dimension_scores,
            role,
        )

        overall_score = round(sum(weighted_breakdown.values()), 1)

        # 3️⃣ Gating
        gating_triggered, gating_reason = self._apply_gating_rule(
            dimension_scores,
            role,
        )

        if gating_triggered:
            hiring_probability = 0.0
        else:
            hiring_probability = self._compute_hiring_probability(overall_score)

        # 4️⃣ Percentile (deterministic analytical)
        percentile = self._compute_percentile(overall_score, role)

        dist_params = ROLE_DISTRIBUTION[role]
        percentile_explanation = (
            f"Percentile computed analytically using role-specific "
            f"normal distribution (μ={dist_params['mean']}, σ={dist_params['std']})."
        )

        # 5️⃣ Confidence
        confidence = self._compute_confidence(per_question_evaluations)

        # 6️⃣ Executive summary
        executive_summary = self._generate_executive_summary(
            overall_score,
            dimension_scores,
        )

        # 7️⃣ Narrative justification (LLM)
        narrative = self._generate_narrative(
            per_question_evaluations,
            dimension_scores,
            interview_type,
            role,
        )

        performance_dimensions = []
        for name, score in dimension_scores.items():

            justification = narrative["dimension_justifications"].get(
                name,
                "Justification unavailable.",
            )

            performance_dimensions.append(
                PerformanceDimension(
                    name=name,
                    score=score,
                    justification=justification,
                )
            )

        return InterviewEvaluation(
            overall_score=overall_score,
            executive_summary=executive_summary,
            performance_dimensions=performance_dimensions,
            hiring_probability=hiring_probability,
            percentile_rank=percentile,
            percentile_explanation=percentile_explanation,
            gating_triggered=gating_triggered,
            gating_reason=gating_reason,
            weighted_breakdown=weighted_breakdown,
            per_question_assessment=per_question_evaluations,
            improvement_suggestions=narrative["improvement_suggestions"],
            confidence=confidence,
        )

    # ---------------------------------------------------------
    # DIMENSION SCORING
    # ---------------------------------------------------------

    def _compute_dimension_scores(
        self,
        questions: List[Question],
        evaluations: List[QuestionEvaluation],
    ) -> Dict[str, float]:

        question_area_map = {q.id: q.area for q in questions}

        AREA_TO_DIMENSION = {
            "technical_background": "Technical Depth",
            "technical_technical_knowledge": "Technical Depth",
            "technical_database": "Technical Depth",
            "technical_coding": "Problem Solving",
            "technical_case_study": "System Design",
            "hr_background": "Communication",
            "hr_technical_knowledge": "Technical Depth",
            "hr_situational": "Communication",
            "hr_brain_teaser": "Problem Solving",
            "hr_analytical": "Problem Solving",
        }

        dimension_map: Dict[str, List[float]] = {}

        for ev in evaluations:
            area = question_area_map.get(ev.question_id)
            if not area:
                continue

            dimension = AREA_TO_DIMENSION.get(area)
            if not dimension:
                continue

            dimension_map.setdefault(dimension, []).append(ev.score)

        result: Dict[str, float] = {}

        for dimension in ALLOWED_DIMENSIONS:
            scores = dimension_map.get(dimension, [])
            if scores:
                result[dimension] = round(sum(scores) / len(scores), 1)
            else:
                result[dimension] = 0.0

        return result

    # ---------------------------------------------------------

    def _compute_weighted_breakdown(
        self,
        dimension_scores: Dict[str, float],
        role: RoleType,
    ) -> Dict[str, float]:

        weights = ROLE_WEIGHTS[role]

        breakdown = {}
        for dim, score in dimension_scores.items():
            weight = weights.get(dim, 0.0)
            breakdown[dim] = round(score * weight, 2)

        return breakdown

    # ---------------------------------------------------------

    def _apply_gating_rule(
        self,
        dimension_scores: Dict[str, float],
        role: RoleType,
    ) -> tuple[bool, str | None]:

        critical_dimensions = {
            RoleType.BACKEND_ENGINEER: ["System Design"],
        }

        critical = critical_dimensions.get(role, [])

        for dim in critical:
            if dimension_scores.get(dim, 0.0) == 0.0:
                return (
                    True,
                    f"Critical dimension '{dim}' scored 0.0 for role '{role.value}'.",
                )

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
        else:
            return 95.0

    # ---------------------------------------------------------

    def _compute_percentile(
        self,
        score: float,
        role: RoleType,
    ) -> float:

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
    ) -> Confidence:

        scores = [q.score for q in evaluations]

        if len(scores) < 2:
            return Confidence(base=0.7, final=0.7)

        variance = statistics.pvariance(scores)

        confidence_value = 1 / (1 + variance / 1000.0)
        confidence_value = round(confidence_value, 2)

        return Confidence(
            base=confidence_value,
            final=confidence_value,
        )

    # ---------------------------------------------------------

    def _generate_executive_summary(
        self,
        overall_score: float,
        dimension_scores: Dict[str, float],
    ) -> str:

        max_score = max(dimension_scores.values())
        min_score = min(dimension_scores.values())
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

    def _generate_narrative(
        self,
        evaluations: List[QuestionEvaluation],
        dimension_scores: Dict[str, float],
        interview_type: InterviewType,
        role: RoleType,
    ) -> Dict:

        prompt = f"""
You are a senior technical interviewer.

Role: {role.value}
Interview type: {interview_type.value}

Here are evaluated answers:
{[e.model_dump() for e in evaluations]}

Dimension scores (deterministically computed):
{dimension_scores}

Provide:

1. A short justification (2-3 sentences) for EACH dimension:
- Technical Depth
- Communication
- Problem Solving
- System Design

2. 3 concise improvement suggestions.

Return STRICT JSON only in this format:

{{
  "dimension_justifications": {{
    "Technical Depth": "...",
    "Communication": "...",
    "Problem Solving": "...",
    "System Design": "..."
  }},
  "improvement_suggestions": ["...", "...", "..."]
}}
"""

        response = self._llm.invoke(prompt)

        try:
            return self._extract_json(response.content)
        except Exception:
            logger.warning("narrative_json_parsing_failed")

            return {
                "dimension_justifications": {
                    name: "Justification unavailable." for name in ALLOWED_DIMENSIONS
                },
                "improvement_suggestions": [
                    "Further technical depth improvement recommended.",
                ],
            }

    # ---------------------------------------------------------

    def _extract_json(self, text: str) -> Dict:

        try:
            return json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")

            if start == -1 or end == -1:
                raise ValueError("No JSON object found")

            return json.loads(text[start : end + 1])
