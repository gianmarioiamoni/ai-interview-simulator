# services/interview_evaluation_service.py

# Interview evaluation service
#
# Responsibility:
# - orchestrates LLM evaluation
# - validates strict JSON
# - enforces mathematical consistency
# - produces immutable InterviewEvaluation

from typing import List
import json

from app.ports.llm_port import LLMPort
from domain.contracts.interview_evaluation import InterviewEvaluation
from domain.contracts.performance_dimension import PerformanceDimension
from domain.contracts.question_evaluation import QuestionEvaluation


MAX_RETRIES = 2


class InterviewEvaluationService:

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

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

                self._verify_consistency(evaluation)

                return self._normalize(evaluation)

            except Exception:
                if attempt == MAX_RETRIES:
                    raise
        
        
    # ---------------------------------------------------------

    def _build_prompt(
        self,
        per_question_evaluations: List[QuestionEvaluation],
        interview_type: str,
        role: str,
    ) -> str:

        return f"""
You are a strict technical interviewer.

Role: {role}
Interview type: {interview_type}

Per-question evaluations:
{[e.model_dump() for e in per_question_evaluations]}

Return STRICT JSON with:
- overall_score (1-10)
- performance_dimensions (exactly 4)
- hiring_probability (0-100)
- improvement_suggestions (list)
- confidence (0-1)
"""

    # ---------------------------------------------------------

    def _verify_consistency(self, evaluation: InterviewEvaluation) -> None:

        computed = self._compute_overall_score(evaluation.performance_dimensions)

        if abs(computed - evaluation.overall_score) > 0.5:
            raise ValueError("Inconsistent overall score")

    # ---------------------------------------------------------

    def _normalize(self, evaluation: InterviewEvaluation) -> InterviewEvaluation:

        overall = self._compute_overall_score(evaluation.performance_dimensions)
        hiring_probability = self._compute_hiring_probability(overall)

        return evaluation.model_copy(
            update={
                "overall_score": overall,
                "hiring_probability": hiring_probability,
            }
        )

    # ---------------------------------------------------------

    def _compute_overall_score(self, dimensions: List[PerformanceDimension]) -> float:

        raw_avg = sum(d.score for d in dimensions) / len(dimensions)
        bounded = max(1.0, min(10.0, raw_avg))
        return round(bounded, 1)

    # ---------------------------------------------------------

    def _compute_hiring_probability(self, overall_score: float) -> float:
        return round((overall_score / 10.0) * 100, 1)
