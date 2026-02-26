# services/interview_evaluation_service.py

# Interview evaluation service
#
# Responsibility:
# - orchestrates LLM evaluation
# - validates strict JSON
# - enforces mathematical consistency
# - enforces schema governance
# - applies deterministic normalization
# - applies deterministic confidence computation
# - provides deterministic fallback strategy

from typing import List

import json
import statistics
import logging

from app.ports.llm_port import LLMPort
from domain.contracts.interview_evaluation import InterviewEvaluation
from domain.contracts.performance_dimension import PerformanceDimension
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.confidence import Confidence

logger = logging.getLogger(__name__)


MAX_RETRIES = 2

ALLOWED_DIMENSIONS = {
    "Technical Depth",
    "Communication",
    "Problem Solving",
    "System Design",
}


class InterviewEvaluationService:

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    # ---------------------------------------------------------

    def evaluate(
        self,
        per_question_evaluations: List[QuestionEvaluation],
        interview_type: str,
        role: str,
    ) -> InterviewEvaluation:

        prompt = self._build_prompt(
            per_question_evaluations,
            interview_type,
            role,
        )

        for attempt in range(MAX_RETRIES + 1):

            logger.info(
                "evaluation_attempt",
                extra={
                    "attempt": attempt,
                    "interview_type": interview_type,
                    "role": role,
                },
            )

            response = self._llm.invoke(prompt)

            try:
                parsed = self._extract_json_object(response.content)

                evaluation = InterviewEvaluation.model_validate(parsed)

                self._enforce_schema_rules(evaluation)
                self._verify_consistency(evaluation)

                normalized = self._normalize(evaluation)
                logger.info(
                    "evaluation_success",
                    extra={
                        "attempt": attempt,
                        "normalized_score": normalized.overall_score,
                        "confidence": evaluation.confidence,
                    },
                )

                return normalized

            except Exception as e:
                logger.warning(
                    "evaluation_retry",
                    extra={
                        "attempt": attempt,
                        "error_type": type(e).__name__,
                    },
                )

                if attempt == MAX_RETRIES:
                    logger.error(
                        "evaluation_fallback_triggered",
                        extra={
                            "reason": type(e).__name__,
                        },
                    )
                    return self._fallback_evaluation(per_question_evaluations)

        # Should never be reached
        return self._fallback_evaluation(per_question_evaluations)

    # ---------------------------------------------------------

    def _build_prompt(
        self,
        per_question_evaluations: List[QuestionEvaluation],
        interview_type: str,
        role: str,
    ) -> str:

        return f"""
You are a strict and deterministic technical interviewer.

Role: {role}
Interview type: {interview_type}

You MUST return valid JSON only.
Do not include explanations or text outside JSON.

Allowed performance dimensions (exactly these 4):
- Technical Depth
- Communication
- Problem Solving
- System Design

Per-question evaluations:
{[e.model_dump() for e in per_question_evaluations]}

Return STRICT JSON with this structure:

{{
  "overall_score": float (0-100),
  "performance_dimensions": [
    {{
      "name": one of allowed dimensions,
      "score": float (0-100),
      "justification": string
    }}
  ],
  "hiring_probability": float (0-100),
  "per_question_assessment": list,
  "improvement_suggestions": list of strings,
}}

Constraints:
- Must include exactly 4 performance dimensions
- No extra fields
- No missing fields
"""

    # ---------------------------------------------------------

    def _enforce_schema_rules(self, evaluation: InterviewEvaluation) -> None:

        # Exactly 4 dimensions
        if len(evaluation.performance_dimensions) != 4:
            raise ValueError("Must contain exactly 4 performance dimensions")

        names = [d.name for d in evaluation.performance_dimensions]

        # Unique names
        if len(set(names)) != 4:
            raise ValueError("Duplicate performance dimension names")

        # Must match allowed set exactly
        if set(names) != ALLOWED_DIMENSIONS:
            raise ValueError("Invalid performance dimension set")

    # ---------------------------------------------------------

    def _verify_consistency(self, evaluation: InterviewEvaluation) -> None:

        computed = self._compute_overall_score(evaluation.performance_dimensions)

        if abs(computed - evaluation.overall_score) > 0.5:
            raise ValueError("Inconsistent overall score")

    # ---------------------------------------------------------

    def _normalize(self, evaluation: InterviewEvaluation) -> InterviewEvaluation:

        overall = self._compute_overall_score(evaluation.performance_dimensions)
        confidence_value = self._compute_confidence(evaluation.performance_dimensions)
        confidence = Confidence(base=confidence_value, final=confidence_value)
        hiring_probability = self._compute_hiring_probability(overall)

        return evaluation.model_copy(
            update={
                "overall_score": overall,
                "confidence": confidence,
                "hiring_probability": hiring_probability,
            }
        )

    # ---------------------------------------------------------

    def _compute_overall_score(
        self,
        dimensions: List[PerformanceDimension],
    ) -> float:

        raw_avg = sum(d.score for d in dimensions) / len(dimensions)
        bounded = max(0.0, min(100.0, raw_avg))
        return round(bounded, 1)

    # ---------------------------------------------------------

    def _compute_confidence(
        self,
        dimensions: List[PerformanceDimension],
    ) -> float:

        scores = [d.score for d in dimensions]

        if len(scores) < 2:
            return 0.5

        variance = statistics.pvariance(scores)

        # Higher variance -> lower confidence
        confidence = max(0.0, 1.0 - (variance / 2500.0))

        return round(confidence, 2)

    # ---------------------------------------------------------

    def _fallback_evaluation(
        self,
        per_question_evaluations: List[QuestionEvaluation],
    ) -> InterviewEvaluation:

        if not per_question_evaluations:
            overall = 50.0
        else:
            avg_score = sum(q.score for q in per_question_evaluations) / len(
                per_question_evaluations
            )
            overall = round(avg_score, 1)

        dimensions = [
            {
                "name": name,
                "score": overall,
                "justification": "Deterministic fallback evaluation",
            }
            for name in ALLOWED_DIMENSIONS
        ]

        return InterviewEvaluation(
            overall_score=overall,
            performance_dimensions=dimensions,
            hiring_probability=self._compute_hiring_probability(overall),
            per_question_assessment=per_question_evaluations,
            improvement_suggestions=["Manual review recommended"],
            confidence=Confidence(base=0.3, final=0.3),
        )

    # ---------------------------------------------------------

    def _extract_json_object(self, text: str) -> dict:

        # First try direct parsing
        try:
            return json.loads(text)
        except Exception:
            pass

        # Try to extract first JSON object from text
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:
            logger.warning("json_extraction_failed")
            raise ValueError("No JSON object found in response")

        candidate = text[start : end + 1]

        logger.info("json_extraction_used")

        return json.loads(candidate)

    # ---------------------------------------------------------

    def _compute_hiring_probability(self, score: float) -> float:
        # Piecewise enterprise-style hiring probability mapping.
        # Score expected in range 0-100.

        if score < 50:
            return 0.0
        elif score < 65:
            return 30.0
        elif score < 75:
            return 55.0
        elif score < 85:
            return 75.0
        else:
            return 90.0