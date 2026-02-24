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

from app.ports.llm_port import LLMPort
from domain.contracts.interview_evaluation import InterviewEvaluation
from domain.contracts.performance_dimension import PerformanceDimension
from domain.contracts.question_evaluation import QuestionEvaluation


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

            response = self._llm.invoke(prompt)

            try:
                parsed = json.loads(response.content)

                evaluation = InterviewEvaluation.model_validate(parsed)

                self._enforce_schema_rules(evaluation)
                self._verify_consistency(evaluation)

                return self._normalize(evaluation)

            except Exception:
                if attempt == MAX_RETRIES:
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
  "overall_score": float (1-10),
  "performance_dimensions": [
    {{
      "name": one of allowed dimensions,
      "score": float (1-10),
      "justification": string
    }}
  ],
  "hiring_probability": float (0-100),
  "per_question_assessment": list,
  "improvement_suggestions": list of strings,
  "confidence": float (0-1)
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

        # Confidence bounds
        if evaluation.confidence < 0.0 or evaluation.confidence > 1.0:
            raise ValueError("Invalid confidence value")

    # ---------------------------------------------------------

    def _verify_consistency(self, evaluation: InterviewEvaluation) -> None:

        computed = self._compute_overall_score(evaluation.performance_dimensions)

        if abs(computed - evaluation.overall_score) > 0.5:
            raise ValueError("Inconsistent overall score")

    # ---------------------------------------------------------

    def _normalize(self, evaluation: InterviewEvaluation) -> InterviewEvaluation:

        overall = self._compute_overall_score(evaluation.performance_dimensions)
        hiring_probability = self._compute_hiring_probability(overall)
        confidence = self._compute_confidence(evaluation.performance_dimensions)

        return evaluation.model_copy(
            update={
                "overall_score": overall,
                "hiring_probability": hiring_probability,
                "confidence": confidence,
            }
        )

    # ---------------------------------------------------------

    def _compute_overall_score(
        self,
        dimensions: List[PerformanceDimension],
    ) -> float:

        raw_avg = sum(d.score for d in dimensions) / len(dimensions)
        bounded = max(1.0, min(10.0, raw_avg))
        return round(bounded, 1)

    # ---------------------------------------------------------

    def _compute_hiring_probability(self, overall_score: float) -> float:
        return round((overall_score / 10.0) * 100, 1)

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
        confidence = max(0.0, 1.0 - (variance / 25.0))

        return round(confidence, 2)

    # ---------------------------------------------------------

    def _fallback_evaluation(
        self,
        per_question_evaluations: List[QuestionEvaluation],
    ) -> InterviewEvaluation:

        if not per_question_evaluations:
            overall = 5.0
        else:
            avg_score = sum(q.score for q in per_question_evaluations) / len(
                per_question_evaluations
            )
            overall = round((avg_score / 100.0) * 10.0, 1)

        dimensions = [
            PerformanceDimension(
                name=name,
                score=overall,
                justification="Deterministic fallback evaluation",
            )
            for name in ALLOWED_DIMENSIONS
        ]

        return InterviewEvaluation(
            overall_score=overall,
            performance_dimensions=dimensions,
            hiring_probability=self._compute_hiring_probability(overall),
            per_question_assessment=per_question_evaluations,
            improvement_suggestions=["Manual review recommended"],
            confidence=0.3,
        )
