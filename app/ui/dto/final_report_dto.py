# app/ui/dto/final_report_dto.py

from typing import List, Dict, Optional
from pydantic import BaseModel

from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from app.ui.dto.question_assessment_dto import QuestionAssessmentDTO
from app.ui.utils.error_formatter import simplify_execution_error

from domain.contracts.confidence import Confidence
from domain.contracts.test_execution_result import TestStatus
from domain.contracts.execution_result import ExecutionResult
from domain.contracts.interview_state import InterviewState


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
    def from_state(cls, state: InterviewState):

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

            attempts = state.attempts_by_question.get(q.id, 0)

            ai_hint_explanation: Optional[str] = None
            ai_hint_suggestion: Optional[str] = None

            # ======================================================
            # WRITTEN
            # ======================================================

            if result.evaluation and not result.execution:

                score = result.evaluation.score
                feedback = result.evaluation.feedback

            # ======================================================
            # EXECUTION
            # ======================================================

            elif result.execution:

                exec_res = result.execution
                execution_status = exec_res.status.value

                if exec_res.total_tests == 0 and not exec_res.success:

                    execution_status = "RUNTIME_ERROR"
                    score = 0

                else:

                    passed_tests = exec_res.passed_tests
                    total_tests = exec_res.total_tests

                    if exec_res.total_tests:
                        score = (exec_res.passed_tests / exec_res.total_tests) * 100
                    elif exec_res.success:
                        score = 100
                    else:
                        score = 0

                feedback = (
                    simplify_execution_error(exec_res.error)
                    or "Execution evaluated automatically."
                )

            # ======================================================
            # AI HINT (READ ONLY)
            # ======================================================

            if result.ai_hint:
                ai_hint_explanation = result.ai_hint.explanation
                ai_hint_suggestion = result.ai_hint.suggestion

            # ======================================================
            # DTO
            # ======================================================

            q_assessment = QuestionAssessmentDTO(
                question_id=q.id,
                score=score,
                feedback=feedback,
                passed_tests=passed_tests,
                total_tests=total_tests,
                execution_status=execution_status,
                attempts=attempts,
                ai_hint_explanation=ai_hint_explanation,
                ai_hint_suggestion=ai_hint_suggestion,
            )

            assert isinstance(q_assessment.feedback, str)
            assert isinstance(q_assessment.ai_hint_explanation, (str, type(None)))
            assert isinstance(q_assessment.ai_hint_suggestion, (str, type(None)))

            question_assessments.append(q_assessment)

        # =========================================================
        # DIMENSIONS
        # =========================================================

        fe = state.final_evaluation

        if fe is None:
            raise RuntimeError("Final evaluation missing")

        dimension_scores = [
            DimensionScoreDTO(
                name=dim.name,
                score=dim.score,
                max_score=100,
            )
            for dim in fe.performance_dimensions
        ]

        # =========================================================
        # IMPROVEMENTS
        # =========================================================

        improvements = [
            f"Improve performance on question {q.question_id} (score {q.score:.1f}/100)."
            for q in question_assessments
            if q.score < 60
        ]

        # =========================================================
        # TOKENS
        # =========================================================

        tokens = sum(
            getattr(r.evaluation, "tokens_used", 0)
            for r in state.results_by_question.values()
            if r.evaluation
        )

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

    # =========================================================
    # FAILED TESTS
    # =========================================================

    @staticmethod
    def _format_failed_tests(exec_res: ExecutionResult) -> str:
        if not exec_res or not exec_res.test_results:
            return "None"

        failed = [t for t in exec_res.test_results if t.status != TestStatus.PASSED]

        if not failed:
            return "None"

        return "\n".join(
            [
                f"Input: {t.args} | Expected: {t.expected} | Actual: {t.actual}"
                for t in failed[:2]
                if t.status != TestStatus.ERROR
            ]
        )
