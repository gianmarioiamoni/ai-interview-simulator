# services/interview_evaluation_service.py

from typing import List, Dict
import statistics
import logging
import json
import math

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

        overall_score = self._compute_weighted_overall(
            dimension_scores,
            role,
        )

        hiring_probability = (
            0.0
            if self._apply_gating_rule(dimension_scores, role)
            else self._compute_hiring_probability(overall_score)
        )

        executive_summary = self._generate_executive_summary(
            overall_score,
            dimension_scores,
        )

        confidence = self._compute_confidence(per_question_evaluations)

        narrative = self._generate_narrative(
            per_question_evaluations,
            dimension_scores,
            interview_type,
            role,
        )

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
            result[dimension] = round(sum(scores) / len(scores), 1) if scores else 0.0

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

    def _apply_gating_rule(
        self,
        dimension_scores: Dict[str, float],
        role: str,
    ) -> bool:

        critical_dimensions = {
            "backend_engineer": ["System Design"],
        }

        critical = critical_dimensions.get(role, [])

        return any(dimension_scores[d] == 0 for d in critical)

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

    def _compute_percentile(self, score: float) -> float:
        mean = 60
        std = 15
        z = (score - mean) / std
        percentile = 0.5 * (1 + math.erf(z / math.sqrt(2)))
        return round(percentile * 100, 1)

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

        return Confidence(base=confidence_value, final=confidence_value)

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
