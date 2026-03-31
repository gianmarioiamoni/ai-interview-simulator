# app/ui/mappers/interview_state_mapper.py

from domain.contracts.interview_state import InterviewState

from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.question_dto import QuestionDTO
from app.ui.dto.final_report_dto import FinalReportDTO


class InterviewStateMapper:

    # =========================================================
    # SESSION DTO
    # =========================================================

    def to_session_dto(self, state: InterviewState) -> InterviewSessionDTO:

        question = state.current_question

        question_dto = None
        current_area = None

        if question is not None:

            index = state.current_question_index + 1
            total = len(state.questions)

            question_dto = QuestionDTO(
                question_id=question.id,
                text=question.prompt,
                type=question.type.value,
                area=question.area.value,
                index=index,
                total=total,
            )

            current_area = question.area.value

        return InterviewSessionDTO(
            session_id=state.interview_id,
            current_question=question_dto,
            is_completed=state.progress.value == "completed",
            current_area=current_area,
        )

    # =========================================================
    # FINAL REPORT DTO
    # =========================================================

    def to_final_report_dto(
        self,
        state: InterviewState,
    ) -> FinalReportDTO:

        final_evaluation = state.final_evaluation

        if final_evaluation is None:
            raise ValueError("Final evaluation is required")

        # Delegate entirely to DTO factory
        return FinalReportDTO.from_components(
            state=state,
            final_evaluation=final_evaluation,
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
