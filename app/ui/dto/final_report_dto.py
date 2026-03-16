# app/ui/dto/final_report_dto.py

from typing import List, Dict, Optional
from pydantic import BaseModel

from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from app.ui.dto.question_assessment_dto import QuestionAssessmentDTO
from app.ui.utils.error_formatter import simplify_execution_error

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

        question_assessments: List[QuestionAssessmentDTO] = []

        for q in state.questions:

            result = state.results_by_question.get(q.id)

            if result is None:
                continue

            score = 0.0
            feedback = ""
            passed_tests: Optional[int] = None
            total_tests: Optional[int] = None
            execution_status: Optional[str] = None

            # ---------------------------------------------------------
            # LLM Evaluation
            # ---------------------------------------------------------

            if result.evaluation:

                score = result.evaluation.score
                feedback = result.evaluation.feedback

            # ---------------------------------------------------------
            # Execution-based evaluation (coding / SQL)
            # ---------------------------------------------------------

            elif result.execution:

                exec_res = result.execution

                execution_status = exec_res.status.value

                # runtime error before tests
                if exec_res.total_tests == 0 and not exec_res.success:

                    execution_status = "RUNTIME_ERROR"
                    passed_tests = None
                    total_tests = None
                    score = 0

                else:

                    passed_tests = exec_res.passed_tests
                    total_tests = exec_res.total_tests

                    if exec_res.total_tests and exec_res.total_tests > 0:

                        score = (exec_res.passed_tests / exec_res.total_tests) * 100

                    elif exec_res.success:

                        score = 100

                    else:

                        score = 0

                feedback = (
                    simplify_execution_error(exec_res.error)
                    or "Execution evaluated automatically."
                )

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

        # ---------------------------------------------------------
        # Dimension scores
        # ---------------------------------------------------------

        dimension_scores: List[DimensionScoreDTO] = []

        fe = state.final_evaluation

        if fe:

            for dim in fe.performance_dimensions:

                dimension_scores.append(
                    DimensionScoreDTO(
                        name=dim.name,
                        score=dim.score,
                        max_score=100,
                    )
                )

        # ---------------------------------------------------------
        # Improvement suggestions
        # ---------------------------------------------------------

        improvements: List[str] = []

        for q in question_assessments:

            if q.score < 60:

                improvements.append(
                    f"Improve performance on question {q.question_id} (score {q.score:.1f}/100)."
                )

        # ---------------------------------------------------------
        # Token accounting
        # ---------------------------------------------------------

        tokens = 0

        for r in state.results_by_question.values():

            if r.evaluation and hasattr(r.evaluation, "tokens_used"):

                tokens += r.evaluation.tokens_used

        # ---------------------------------------------------------
        # Safety check
        # ---------------------------------------------------------

        if fe is None:

            raise RuntimeError("Final evaluation missing when generating report")

        # ---------------------------------------------------------
        # DTO creation
        # ---------------------------------------------------------

        return cls(
            overall_score=fe.overall_score,
            hiring_probability=fe.hiring_probability,
            percentile_rank=fe.percentile_rank,
            percentile_explanation=fe.percentile_explanation,
            executive_summary=fe.executive_summary,
            gating_triggered=fe.gating_triggered,
            gating_reason=fe.gating_reason,
            weighted_breakdown=fe.weighted_breakdown,
            dimension_scores=dimension_scores,
            question_assessments=question_assessments,
            improvement_suggestions=improvements,
            total_tokens_used=tokens,
            confidence=fe.confidence,
        )
