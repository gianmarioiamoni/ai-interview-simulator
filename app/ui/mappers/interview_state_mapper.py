# app/ui/mappers/interview_state_mapper.py

ffrom domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType

from app.ui.dto.session_dto import SessionDTO, QuestionDTO
from app.ui.dto.final_report_dto import (
    FinalReportDTO,
    QuestionAssessmentDTO,
    DimensionScoreDTO,
)


class InterviewStateMapper:

    # =========================================================
    # SESSION DTO
    # =========================================================

    def to_session_dto(self, state: InterviewState) -> SessionDTO:

        question = state.current_question

        if question is None:
            return SessionDTO(current_question=None)

        index = state.current_question_index + 1
        total = len(state.questions)

        question_dto = QuestionDTO(
            id=question.id,
            text=question.prompt,
            question_type=question.type.value,
            index=index,
            total=total,
        )

        return SessionDTO(current_question=question_dto)

    # =========================================================
    # FINAL REPORT DTO
    # =========================================================

    def to_final_report_dto(self, state: InterviewState) -> FinalReportDTO:

        question_assessments = []

        # ---------------------------------------------------------
        # Build question assessments
        # ---------------------------------------------------------

        for q in state.questions:

            result = state.results_by_question.get(q.id)

            if result is None:
                continue

            score = 0
            feedback = ""
            passed_tests = None
            total_tests = None
            execution_status = None

            # -----------------------------------------------------
            # WRITTEN QUESTION
            # -----------------------------------------------------

            if result.evaluation is not None:

                score = result.evaluation.score
                feedback = result.evaluation.feedback

            # -----------------------------------------------------
            # CODING / DATABASE QUESTION
            # -----------------------------------------------------

            elif result.execution is not None:

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

        # ---------------------------------------------------------
        # Dimension scores
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Improvement suggestions
        # ---------------------------------------------------------

        improvement_suggestions = self._aggregate_weaknesses(question_assessments)

        # ---------------------------------------------------------
        # Token usage
        # ---------------------------------------------------------

        total_tokens_used = 0

        for result in state.results_by_question.values():

            if result.evaluation and hasattr(result.evaluation, "tokens_used"):

                total_tokens_used += result.evaluation.tokens_used

        # ---------------------------------------------------------
        # Final DTO
        # ---------------------------------------------------------

        return FinalReportDTO(
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
            improvement_suggestions=improvement_suggestions,
            total_tokens_used=total_tokens_used,
            confidence=state.final_evaluation.confidence,
        )

    
    # =========================================================
    # WEAKNESS AGGREGATION
    # =========================================================

    def _aggregate_weaknesses(self, question_assessments):

        improvements = []

        for q in question_assessments:

            if q.score < 60:

                improvements.append(
                    f"Improve performance on question {q.question_id} (score {q.score:.1f}/100)."
                )

        return improvements