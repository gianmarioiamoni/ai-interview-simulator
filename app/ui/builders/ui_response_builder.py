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

        # -----------------------------------------------------
        # SETUP
        # -----------------------------------------------------

        if ui_state.name == "SETUP":
            return UIResponse(state=state)

        # -----------------------------------------------------
        # REPORT
        # -----------------------------------------------------

        if ui_state.name == "REPORT":
            return UIResponse(
                state=state,
                report_output="Report ready",
            )

        # -----------------------------------------------------
        # QUESTION FLOW
        # -----------------------------------------------------

        question = session_dto.current_question

        if question is None:
            # safety fallback
            return UIResponse(state=state)

        attempts = state.get_attempt_for_question(question.question_id)
        can_retry = attempts < MAX_ATTEMPTS

        # -----------------------------------------------------
        # BUILD SECTIONS
        # -----------------------------------------------------

        display = DisplaySection.build(state, question, ui_state, attempts > 0)
        feedback = FeedbackSection.build(state)
        counter = CounterSection.build(question, attempts, MAX_ATTEMPTS)
        buttons = ButtonMapper.map(state, ui_state, can_retry)

        # -----------------------------------------------------
        # DISPLAY CONTENT
        # -----------------------------------------------------

        written_display = display.get("written_display", "")
        coding_display = display.get("coding_display", "")
        database_display = display.get("database_display", "")

        # -----------------------------------------------------
        # VISIBILITY (CRITICO)
        # -----------------------------------------------------

        is_written = bool(written_display)
        is_coding = bool(coding_display)
        is_database = bool(database_display)

        # -----------------------------------------------------
        # EDITOR DEFAULTS
        # -----------------------------------------------------

        editor_value = ""

        if question.type == QuestionType.CODING:
            editor_value = "# Write your solution here"
        elif question.type == QuestionType.DATABASE:
            editor_value = "-- Write your SQL query here"

        # -----------------------------------------------------
        # DEBUG
        # -----------------------------------------------------

        print("\n=== DEBUG UI BUILD ===")
        print("question type:", question.type)
        print("written_display:", bool(written_display))
        print("coding_display:", bool(coding_display))
        print("database_display:", bool(database_display))
        print("counter:", counter)
        print("feedback:", feedback)
        print("buttons:", buttons)
        print("=======================\n")

        # -----------------------------------------------------
        # FINAL RESPONSE
        # -----------------------------------------------------

        return UIResponse(
            state=state,
            # HEADER
            question_counter=counter,
            feedback_markdown=feedback,
            # DISPLAY
            written_display=written_display,
            coding_display=coding_display,
            database_display=database_display,
            written_visible=is_written,
            coding_visible=is_coding,
            database_visible=is_database,
            # BUTTONS
            show_submit=buttons["show_submit"],
            show_submit_interactive=buttons["show_submit_interactive"],
            show_retry=buttons["show_retry"],
            show_next=buttons["show_next"],
            next_label=buttons.get("next_label") or "Next",
            # EDITORS
            written_editor_value=editor_value if is_written else "",
            coding_editor_value=editor_value if is_coding else "",
            database_editor_value=editor_value if is_database else "",
            written_editor_visible=is_written,
            coding_editor_visible=is_coding,
            database_editor_visible=is_database,
        )
