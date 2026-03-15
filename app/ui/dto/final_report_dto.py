from typing import List, Dict, Optional
from pydantic import BaseModel

from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from app.ui.dto.question_assessment_dto import QuestionAssessmentDTO

from domain.contracts.confidence import Confidence


class FinalReportDTO(BaseModel):

    overall_score: float
    hiring_probability: float
    percentile_rank: float
    percentile_explanation: str

    executive_summary: str

    gating_triggered: bool
    gating_reason: Optional[str]

    weighted_breakdown: Dict[str, float]

    dimension_scores: List[DimensionScoreDTO]
    question_assessments: List[QuestionAssessmentDTO]
    improvement_suggestions: List[str]

    total_tokens_used: int

    confidence: Confidence

    # =========================================================
    # Factory
    # =========================================================

    @classmethod
    def from_state(cls, state):

        question_assessments = []

        for q in state.questions:

            result = state.results_by_question.get(q.id)

            if result is None:
                continue

            score = 0
            feedback = ""
            passed_tests = None
            total_tests = None
            execution_status = None

            if result.evaluation:

                score = result.evaluation.score
                feedback = result.evaluation.feedback

            elif result.execution:

                exec_res = result.execution

                passed_tests = exec_res.passed_tests
                total_tests = exec_res.total_tests
                execution_status = exec_res.status.value

                if exec_res.total_tests and exec_res.total_tests > 0:
                    score = (exec_res.passed_tests / exec_res.total_tests) * 100
                else:
                    score = 100 if exec_res.success else 0

                feedback = exec_res.error or "Execution evaluated automatically."

            question_assessments.append(
                QuestionAssessmentDTO(
                    question_id=q.id,
                    score=score,
                    feedback=feedback,
                    passed_tests=passed_tests,
                    total_tests=total_tests,
                    execution_status=execution_status,
                )
            )

        dimension_scores = []

        if state.final_evaluation:

            for dim in state.final_evaluation.performance_dimensions:

                dimension_scores.append(
                    DimensionScoreDTO(
                        name=dim.name,
                        score=dim.score,
                        max_score=100,
                    )
                )

        improvements = []

        for q in question_assessments:
            if q.score < 60:
                improvements.append(
                    f"Improve performance on question {q.question_id} (score {q.score:.1f}/100)."
                )

        tokens = 0

        for r in state.results_by_question.values():

            if r.evaluation and hasattr(r.evaluation, "tokens_used"):
                tokens += r.evaluation.tokens_used

        return cls(
            overall_score=state.final_evaluation.overall_score,
            hiring_probability=state.final_evaluation.hiring_probability,
            percentile_rank=state.final_evaluation.percentile_rank,
            percentile_explanation=state.final_evaluation.percentile_explanation,
            executive_summary=state.final_evaluation.executive_summary,
            gating_triggered=state.final_evaluation.gating_triggered,
            gating_reason=state.final_evaluation.gating_reason,
            weighted_breakdown=state.final_evaluation.weighted_breakdown,
            dimension_scores=dimension_scores,
            question_assessments=question_assessments,
            improvement_suggestions=improvements,
            total_tokens_used=tokens,
            confidence=state.final_evaluation.confidence,
        )
