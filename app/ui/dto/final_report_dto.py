# app/ui/dto/final_report_dto.py

from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from app.ui.dto.question_assessment_dto import QuestionAssessmentDTO
from app.ui.utils.error_formatter import simplify_execution_error

from domain.contracts.feedback.confidence import Confidence
from domain.contracts.execution.test_execution_result import TestStatus
from domain.contracts.execution.execution_result import ExecutionResult
from domain.contracts.interview_state import InterviewState
from domain.contracts.shared.performance_dimension_labels import DIMENSION_LABELS
from domain.contracts.user.role import RoleType


class FinalReportDTO(BaseModel):

    overall_score: float
    hiring_probability: float
    hire_decision: str
    decision_explanation: Dict[str, List[str]] 

    percentile_rank: float
    percentile_explanation: str

    executive_summary: str

    gating_triggered: bool
    gating_reason: Optional[str]

    weighted_breakdown: Dict

    dimension_scores: List[DimensionScoreDTO]
    question_assessments: List[QuestionAssessmentDTO]

    improvement_suggestions: List[str]

    total_tokens_used: int

    confidence: Confidence

    role: RoleType

    @classmethod
    def from_components(cls, state: InterviewState, final_evaluation):
        role = state.role.type

        question_assessments: List[QuestionAssessmentDTO] = []

        for q in state.questions:

            result = state.results_by_question.get(q.id)
            if result is None:
                continue

            score = 0.0
            feedback = ""

            passed_tests = None
            total_tests = None
            execution_status = None

            attempts = state.get_attempt_for_question(q.id)

            ai_hint_explanation = None
            ai_hint_suggestion = None

            if result.evaluation and not result.execution:
                score = result.evaluation.score
                feedback = result.evaluation.feedback

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

            if result.ai_hint:
                ai_hint_explanation = result.ai_hint.explanation
                ai_hint_suggestion = result.ai_hint.suggestion

            question_assessments.append(
                QuestionAssessmentDTO(
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
            )

        # ✅ DIMENSIONS (safe with None)

        dimension_scores: List[DimensionScoreDTO] = []

        for dim in final_evaluation.performance_dimensions:

            score = dim.score if dim.score is not None else 0.0
            is_evaluated = dim.score is not None

            dim_type = next(
                (k for k, v in DIMENSION_LABELS.items() if v == dim.name),
                None,
            )

            contribution = 0.0
            weight = 0.0

            if dim_type and dim_type in final_evaluation.weighted_breakdown:
                contribution = final_evaluation.weighted_breakdown[dim_type]

                if score > 0:
                    weight = round(contribution / score, 2)

            dimension_scores.append(
                DimensionScoreDTO(
                    name=dim.name,
                    score=score,
                    max_score=100,
                    weight=weight,
                    contribution=contribution,
                    is_evaluated=is_evaluated,
                )
            )

        # improvements già arricchiti dal service
        improvements = final_evaluation.improvement_suggestions

        tokens = sum(
            getattr(r.evaluation, "tokens_used", 0)
            for r in state.results_by_question.values()
            if r.evaluation
        )

        return cls(
            overall_score=final_evaluation.overall_score,
            hiring_probability=final_evaluation.hiring_probability,
            hire_decision=final_evaluation.hire_decision.value,
            decision_explanation=final_evaluation.decision_explanation,
            percentile_rank=final_evaluation.percentile_rank,
            percentile_explanation=final_evaluation.percentile_explanation,
            executive_summary=final_evaluation.executive_summary,
            gating_triggered=final_evaluation.gating_triggered,
            gating_reason=final_evaluation.gating_reason,
            weighted_breakdown=final_evaluation.weighted_breakdown,
            dimension_scores=dimension_scores,
            question_assessments=question_assessments,
            improvement_suggestions=improvements,
            total_tokens_used=tokens,
            confidence=final_evaluation.confidence,
            role=role,
        )

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
