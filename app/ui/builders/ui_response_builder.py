# app/ui/builders/ui_response_builder.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType

from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.views.report_view import build_report_markdown
from app.ui.ui_response import UIResponse
from app.ui.ui_state import UIState
from app.ui.state_machine.ui_state_machine import UIStateMachine
from app.ui.mappers.interview_state_mapper import InterviewStateMapper

from app.ui.response.sections.display_section import DisplaySection
from app.ui.response.sections.feedback_section import FeedbackSection
from app.ui.response.sections.counter_section import CounterSection
from app.ui.response.config.button_mapper import ButtonMapper

MAX_ATTEMPTS = 3


class UIResponseBuilder:

    def build(self, state: InterviewState) -> UIResponse:

        mapper = InterviewStateMapper()
        session_dto = mapper.to_session_dto(state)

        ui_state = UIStateMachine.resolve(state)

        if ui_state == UIState.SETUP:
            return self._build_setup(state)

        if ui_state == UIState.REPORT:
            return self._build_report(state)

        if ui_state == UIState.COMPLETION:
            return self._build_completion(state)

        return self._build_question(state, session_dto, ui_state)

    def _build_setup(self, state: InterviewState) -> UIResponse:
        return UIResponse(
            state=state,
            setup_visible=True,
            interview_visible=False,
            show_submit=False,
        )

    def _build_report(self, state: InterviewState) -> UIResponse:

        mapper = InterviewStateMapper()
        report = mapper.to_final_report_dto(state)
        report_md = build_report_markdown(report)

        return UIResponse(
            state=state,
            setup_visible=False,
            report_visible=True,
            report_output=report_md,
        )

    def _build_completion(self, state: InterviewState) -> UIResponse:
        return UIResponse(
            state=state,
            setup_visible=False,
            completion_visible=True,
        )

    def _build_question(
        self,
        state: InterviewState,
        session_dto: InterviewSessionDTO,
        ui_state: UIState,
    ) -> UIResponse:

        question = session_dto.current_question

        attempts = state.get_attempt_for_question(question.question_id)
        can_retry = attempts < MAX_ATTEMPTS

        last_answer = state.get_latest_answer_for_question(question.question_id)

        editor_value = ""

        if last_answer:
            editor_value = last_answer.content
        elif question.type == QuestionType.CODING:
            editor_value = "# Write your solution here"
        elif question.type == QuestionType.DATABASE:
            editor_value = "-- Write your SQL query here"

        is_written = question.type == QuestionType.WRITTEN
        is_coding = question.type == QuestionType.CODING
        is_database = question.type == QuestionType.DATABASE

        display = DisplaySection.build(
            state,
            question,
            ui_state,
            attempts > 0,
        )

        feedback = FeedbackSection.build(state)
        counter = CounterSection.build(question, attempts, MAX_ATTEMPTS)
        buttons = ButtonMapper.map(state, ui_state, can_retry)

        return UIResponse(
            state=state,
            setup_visible=False,
            interview_visible=True,
            written_visible=is_written,
            coding_visible=is_coding,
            database_visible=is_database,
            question_counter=counter,
            feedback_markdown=feedback,
            written_display=display.get("written_display", ""),
            coding_display=display.get("coding_display", ""),
            database_display=display.get("database_display", ""),
            show_submit=buttons["show_submit"],
            show_submit_interactive=buttons["show_submit_interactive"],
            show_retry=buttons["show_retry"],
            show_next=buttons["show_next"],
            next_label=buttons["next_label"],
            written_editor_value=editor_value if is_written else "",
            coding_editor_value=editor_value if is_coding else "",
            database_editor_value=editor_value if is_database else "",
        )
