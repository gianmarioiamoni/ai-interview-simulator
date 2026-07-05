# app/ui/mappers/interview_state_mapper.py

from domain.contracts.interview_state import InterviewState

from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.question_dto import QuestionDTO
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.mappers.interview_area_mapper import InterviewAreaMapper



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

            area = InterviewAreaMapper.to_label(question.area)

            question_dto = QuestionDTO(
                question_id=question.id,
                text=question.prompt,
                type=question.type,
                area=area,
                index=index,
                total=total,
            )

            current_area = area

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

        if state.report is None:
            raise ValueError("state.report is required — report_node must run before presentation")

        final_evaluation = state.interview_evaluation

        if final_evaluation is None:
            raise ValueError("Final evaluation is required")

        return FinalReportDTO.from_components(
            state=state,
            final_evaluation=final_evaluation,
        )

