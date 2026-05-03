# app/ui/builders/ui_response_builder.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType

from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.ui_response import UIResponse
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

        if ui_state.name == "SETUP":
            return UIResponse(state=state)

        if ui_state.name == "REPORT":
            return UIResponse(
                state=state,
                report_output="Report ready",
            )

        question = session_dto.current_question

        attempts = state.get_attempt_for_question(question.question_id)
        can_retry = attempts < MAX_ATTEMPTS

        display = DisplaySection.build(state, question, ui_state, attempts > 0)
        feedback = FeedbackSection.build(state)
        counter = CounterSection.build(question, attempts, MAX_ATTEMPTS)
        buttons = ButtonMapper.map(state, ui_state, can_retry)

        written_display = display.get("written_display", "")
        coding_display = display.get("coding_display", "")
        database_display = display.get("database_display", "")

        editor_value = ""

        if question.type == QuestionType.CODING:
            editor_value = "# Write your solution here"
        elif question.type == QuestionType.DATABASE:
            editor_value = "-- Write your SQL query here"

        return UIResponse(
            state=state,
            question_counter=counter,
            feedback_markdown=feedback,
            written_display=written_display,
            coding_display=coding_display,
            database_display=database_display,
            show_submit=buttons["show_submit"],
            show_submit_interactive=buttons["show_submit_interactive"],
            show_retry=buttons["show_retry"],
            show_next=buttons["show_next"],
            next_label=buttons["next_label"],
            written_editor_value=editor_value if written_display else "",
            coding_editor_value=editor_value if coding_display else "",
            database_editor_value=editor_value if database_display else "",
        )
