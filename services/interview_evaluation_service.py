# services/interview_evaluation_service.py

from typing import List, Dict
import statistics
import logging
import json
import random

from app.ports.llm_port import LLMPort
from domain.contracts.interview_evaluation import InterviewEvaluation
from domain.contracts.performance_dimension import PerformanceDimension
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.confidence import Confidence
from domain.contracts.question import Question
from domain.contracts.interview_area import InterviewArea

logger = logging.getLogger(__name__)


# -----------------------------------------
# Canonical Performance Dimensions
# -----------------------------------------

ALLOWED_DIMENSIONS = [
    "Technical Depth",
    "Communication",
    "Problem Solving",
    "System Design",
]

# -----------------------------------------
# InterviewArea → Performance Dimension
# -----------------------------------------

AREA_TO_DIMENSION = {
    InterviewArea.TECH_TECHNICAL_KNOWLEDGE: "Technical Depth",
    InterviewArea.TECH_DATABASE: "Technical Depth",
    InterviewArea.TECH_BACKGROUND: "Technical Depth",
    InterviewArea.TECH_CODING: "Problem Solving",
    InterviewArea.TECH_CASE_STUDY: "System Design",
    InterviewArea.HR_BACKGROUND: "Communication",
    InterviewArea.HR_SITUATIONAL: "Communication",
    InterviewArea.HR_ANALYTICAL: "Problem Solving",
    InterviewArea.HR_BRAIN_TEASER: "Problem Solving",
    InterviewArea.HR_TECHNICAL_KNOWLEDGE: "Technical Depth",
}

# -----------------------------------------
# Role weights
# -----------------------------------------

ROLE_WEIGHTS = {
    "backend_engineer": {
        "Technical Depth": 0.35,
        "System Design": 0.30,
        "Problem Solving": 0.20,
        "Communication": 0.15,
    },
    "frontend_engineer": {
        "Technical Depth": 0.30,
        "System Design": 0.20,
        "Problem Solving": 0.25,
        "Communication": 0.25,
    },
}


class InterviewEvaluationService:

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    # =========================================================
    # PUBLIC API
    # =========================================================

    def evaluate(
        self,
        per_question_evaluations: List[QuestionEvaluation],
        questions: List[Question],
        interview_type: str,
        role: str,
    ) -> InterviewEvaluation:

        dimension_scores = self._compute_dimension_scores(
            questions,
            per_question_evaluations,
        )

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

        executive_summary = self._generate_executive_summary(
            overall_score,
            dimension_scores,
        )

        percentile = self._compute_percentile(overall_score)
        percentile_explanation = (
            "Percentile computed via Monte Carlo simulation "
            "using role-specific synthetic score distribution."
        )

        confidence = self._compute_confidence(per_question_evaluations)

        narrative = self._generate_narrative(
            per_question_evaluations,
            dimension_scores,
            interview_type,
            role,
        )

        executive_summary = self._generate_executive_summary(
            overall_score,
            dimension_scores,
        )

        confidence = self._compute_confidence(per_question_evaluations)

        performance_dimensions = [
            PerformanceDimension(
                name=name,
                score=score,
                justification=narrative["dimension_justifications"].get(
                    name,
                    "Justification unavailable.",
                ),
            )
            for name, score in dimension_scores.items()
        ]

        return InterviewEvaluation(
            overall_score=overall_score,
            executive_summary=executive_summary,
            performance_dimensions=performance_dimensions,
            hiring_probability=hiring_probability,
            percentile_rank=self._compute_percentile(overall_score),
            per_question_assessment=per_question_evaluations,
            improvement_suggestions=narrative["improvement_suggestions"],
            confidence=confidence,
        )

    # =========================================================
    # DETERMINISTIC CORE
    # =========================================================

    def _compute_dimension_scores(
        self,
        questions: List[Question],
        evaluations: List[QuestionEvaluation],
    ) -> Dict[str, float]:

        question_area_map = {q.id: q.area for q in questions}

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
                avg = sum(scores) / len(scores)
                result[dimension] = round(avg, 1)
            else:
                result[dimension] = 0.0

        return result

    def _compute_weighted_overall(
        self,
        dimension_scores: Dict[str, float],
        role: str,
    ) -> float:

        weights = ROLE_WEIGHTS.get(role)

        if not weights:
            avg = sum(dimension_scores.values()) / len(dimension_scores)
            return round(avg, 1)

        weighted = sum(
            dimension_scores[dim] * weights.get(dim, 0) for dim in dimension_scores
        )

        return round(weighted, 1)

    def _compute_weighted_breakdown(
        self,
        dimension_scores: Dict[str, float],
        role: str,
    ) -> Dict[str, float]:

        weights = ROLE_WEIGHTS.get(role)

        if not weights:
            avg = sum(dimension_scores.values()) / len(dimension_scores)
            return {"average": round(avg, 1)}

        breakdown: Dict[str, float] = {}

        for dim, score in dimension_scores.items():
            weight = weights.get(dim, 0.0)
            breakdown[dim] = round(score * weight, 2)

        return breakdown

    def _apply_gating_rule(
        self,
        dimension_scores: Dict[str, float],
        role: str,
    ) -> tuple[bool, str | None]:

        critical_dimensions = {
            "backend_engineer": ["System Design"],
        }

        critical = critical_dimensions.get(role, [])

        for dimension in critical:
            if dimension_scores.get(dimension, 0.0) == 0.0:
                return True, (
                    f"Gating triggered: critical dimension '{dimension}' "
                    f"scored 0.0 for role '{role}'."
                )

        return False, None

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

    def _compute_percentile(self, score: float, role: str) -> float:

        role_distribution = {
            "backend_engineer": (65, 12),
            "frontend_engineer": (63, 13),
        }

        mean, std = role_distribution.get(role, (60, 15))

        sample_size = 10000

        simulated_scores = [
            random.gauss(mean, std) 
            for _ in range(sample_size)
        ]

        # Clamp simulated scores to 0–100
        simulated_scores = [
            max(0.0, min(100.0, s)) 
            for s in simulated_scores
        ]

        below = sum(1 for s in simulated_scores if s <= score)

        percentile = (below / sample_size) * 100

        return round(percentile, 1)

    def _compute_confidence(
        self,
        evaluations: List[QuestionEvaluation],
    ) -> Confidence:

        scores = [q.score for q in evaluations]

        if len(scores) < 2:
            return Confidence(base=0.75, final=0.75)

        variance = statistics.pvariance(scores)

        # Max theoretical variance for 0-100 scale
        max_variance = 2500.0

        normalized_variance = min(variance / max_variance, 1.0)
        stability_index = 1.0 - normalized_variance
        stability_index = round(max(0.0, stability_index), 2)

        return Confidence(
            base=stability_index,
            final=stability_index,
        )

    # =========================================================
    # Narrative
    # =========================================================

    def _generate_narrative(
        self,
        evaluations: List[QuestionEvaluation],
        dimension_scores: Dict[str, float],
        interview_type: str,
        role: str,
    ) -> Dict:

        prompt = f"""
You are a senior technical interviewer.

Role: {role}
Interview type: {interview_type}

Evaluations:
{[e.model_dump() for e in evaluations]}

Dimension scores:
{dimension_scores}

Return STRICT JSON:
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
            return {
                "dimension_justifications": {
                    d: "Justification unavailable." for d in ALLOWED_DIMENSIONS
                },
                "improvement_suggestions": [
                    "Further structured technical preparation recommended."
                ],
            }

    def _extract_json(self, text: str) -> Dict:
        try:
            return json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            return json.loads(text[start : end + 1])

    def _generate_executive_summary(
        self,
        overall_score: float,
        dimension_scores: Dict[str, float],
    ) -> str:

        spread = max(dimension_scores.values()) - min(dimension_scores.values())

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
