# services/interview_evaluation_service.py

# Interview evaluation service
#
# Enterprise deterministic core version.
#
# Responsibility:
# - deterministic scoring engine
# - deterministic hiring probability
# - deterministic confidence
# - LLM only for qualitative justification

from typing import List, Dict
import statistics
import logging
import json

from app.ports.llm_port import LLMPort
from domain.contracts.interview_evaluation import InterviewEvaluation
from domain.contracts.performance_dimension import PerformanceDimension
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.confidence import Confidence
from domain.contracts.question import Question

logger = logging.getLogger(__name__)

ALLOWED_DIMENSIONS = [
    "Technical Depth",
    "Communication",
    "Problem Solving",
    "System Design",
]


class InterviewEvaluationService:

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------

    def evaluate(
        self,
        questions: List[Question],
        per_question_evaluations: List[QuestionEvaluation],
        interview_type: str,
        role: str,
    ) -> InterviewEvaluation:

        if not per_question_evaluations:
            raise ValueError("Cannot evaluate interview without question evaluations")

        # 1️⃣ Deterministic numeric engine
        dimension_scores = self._compute_dimension_scores(
            questions,
            per_question_evaluations,
        )

        overall_score = self._compute_overall_score(per_question_evaluations)
        hiring_probability = self._compute_hiring_probability(overall_score)
        confidence = self._compute_confidence(per_question_evaluations)

        # 2️⃣ LLM narrative generation
        narrative = self._generate_narrative(
            per_question_evaluations,
            dimension_scores,
            interview_type,
            role,
        )

        # 3️⃣ Inject justifications into dimension objects
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

        executive_summary = self._generate_executive_summary(
            overall_score,
            dimension_scores,
        )

        return InterviewEvaluation(
            overall_score=overall_score,
            performance_dimensions=performance_dimensions,
            hiring_probability=hiring_probability,
            per_question_assessment=per_question_evaluations,
            improvement_suggestions=narrative["improvement_suggestions"],
            confidence=confidence,
        )

    # ---------------------------------------------------------
    # DETERMINISTIC CORE
    # ---------------------------------------------------------

    def _compute_dimension_scores(
        self,
        questions: List[Question],
        evaluations: List[QuestionEvaluation],
    ) -> Dict[str, float]:

        # Build question_id → area map
        question_area_map = {q.id: q.area for q in questions}

        # Area → dimension mapping
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

        # dimension -> list of scores
        dimension_map: Dict[str, List[float]] = {}

        for ev in evaluations:

            area = question_area_map.get(ev.question_id)
            if not area:
                continue

            dimension = AREA_TO_DIMENSION.get(area)
            if not dimension:
                continue

            dimension_map.setdefault(dimension, []).append(ev.score)

        # Ensure all dimensions exist
        result: Dict[str, float] = {}

        for dimension in ALLOWED_DIMENSIONS:

            scores = dimension_map.get(dimension, [])

            if scores:
                avg = sum(scores) / len(scores)
                result[dimension] = round(avg, 1)
            else:
                result[dimension] = 0.0

        return result

    # ---------------------------------------------------------

    def _compute_overall_score(
        self,
        evaluations: List[QuestionEvaluation],
    ) -> float:

        avg = sum(q.score for q in evaluations) / len(evaluations)
        bounded = max(0.0, min(100.0, avg))
        return round(bounded, 1)

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

    def _compute_confidence(
        self,
        evaluations: List[QuestionEvaluation],
    ) -> Confidence:

        scores = [q.score for q in evaluations]

        if len(scores) < 2:
            return Confidence(base=0.7, final=0.7)

        variance = statistics.pvariance(scores)

        # smoother stability mapping
        # reduces extreme swings in confidence
        # higher variance -> lower confidence
        confidence_value = 1 / (1 + variance / 1000.0)
        confidence_value = round(confidence_value, 2)

        return Confidence(
            base=confidence_value,
            final=confidence_value,
        )

    # ---------------------------------------------------------
    # LLM NARRATIVE GENERATION
    # ---------------------------------------------------------

    def _generate_narrative(
        self,
        evaluations: List[QuestionEvaluation],
        dimension_scores: List[PerformanceDimension],
        interview_type: str,
        role: str,
    ) -> Dict:

        prompt = f"""
You are a senior technical interviewer.

Role: {role}
Interview type: {interview_type}

Here are evaluated answers:
{[e.model_dump() for e in evaluations]}

Dimension scores (already computed deterministically):
{dimension_scores}

Provide:

1. A short justification (2-3 sentences) for EACH of these dimensions:
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
            base = "The candidate demonstrated mixed performance across evaluated areas."
        else:
            base = "The candidate demonstrated significant gaps in key competency areas."

        if spread > 60:
            stability = "Performance was highly inconsistent across dimensions."
        elif spread > 30:
            stability = "Some variability across dimensions was observed."
        else:
            stability = "Performance was relatively consistent across areas."

        return f"{base} {stability}"