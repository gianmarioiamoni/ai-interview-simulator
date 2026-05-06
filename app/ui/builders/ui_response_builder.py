# app/ui/builders/ui_response_builder.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType

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

        print("\n=== UI RESPONSE BUILDER DEBUG ===")
        print("ui_state:", ui_state)

        # =====================================================
        # SETUP
        # =====================================================
        if ui_state.name == "SETUP":
            return UIResponse(
                state=state,
                # SETUP COMPONENTS
                role_visible=True,
                interview_type_visible=True,
                company_visible=True,
                language_visible=True,
                start_button_visible=True,
                # TITLE
                page_title="## Configure Your Interview",
            )

        # =====================================================
        # REPORT
        # =====================================================
        if ui_state.name == "REPORT":
            return UIResponse(
                state=state,
                # HIDE SETUP
                role_visible=False,
                interview_type_visible=False,
                company_visible=False,
                language_visible=False,
                start_button_visible=False,
                # CONTENT
                page_title="## Final Report",
                report_output="Report ready",
            )

        # =====================================================
        # QUESTION / FEEDBACK FLOW
        # =====================================================
        question = session_dto.current_question

        if question is None:
            return UIResponse(
                state=state,
                # HIDE SETUP
                role_visible=False,
                interview_type_visible=False,
                company_visible=False,
                language_visible=False,
                start_button_visible=False,
            )

        # =====================================================
        # DOMAIN DATA
        # =====================================================
        attempts = state.get_attempt_for_question(question.question_id)
        can_retry = attempts < MAX_ATTEMPTS

        display = DisplaySection.build(state, question, ui_state, attempts > 0)
        feedback = FeedbackSection.build(state)
        counter = CounterSection.build(question, attempts, MAX_ATTEMPTS)
        buttons = ButtonMapper.map(state, ui_state, can_retry)

        # =====================================================
        # DISPLAY CONTENT
        # =====================================================
        written_display = f"<div>{display.get('written_display', '')}</div>"
        coding_display = display.get("coding_display", "")
        database_display = display.get("database_display", "")

        print("FINAL WRITTEN DISPLAY:", written_display)
        print("FINAL CODING DISPLAY:", coding_display)
        print("FINAL DATABASE DISPLAY:", database_display)

        # =====================================================
        # TYPE FLAGS
        # =====================================================
        is_written = question.type == QuestionType.WRITTEN
        is_coding = question.type == QuestionType.CODING
        is_database = question.type == QuestionType.DATABASE

        print(
            "VISIBILITY FLAGS → written:",
            is_written,
            "coding:",
            is_coding,
            "database:",
            is_database,
        )

        print("QUESTION TYPE RAW:", question.type, type(question.type))

        # =====================================================
        # TITLE
        # =====================================================
        if isinstance(question.area, str):
            area_label = question.area
        else:
            area_label = question.area.name.replace("_", " ").title()

        page_title = f"## {area_label}"

        # =====================================================
        # EDITOR DEFAULTS
        # =====================================================
        editor_value = ""

        if is_coding:
            editor_value = "# Write your solution here"
        elif is_database:
            editor_value = "-- Write your SQL query here"

        # =====================================================
        # BUTTON LABEL
        # =====================================================
        if is_coding:
            submit_label = "Run Code"
        elif is_database:
            submit_label = "Run Query"
        else:
            submit_label = "Submit Answer"

        # =====================================================
        # FINAL RESPONSE
        # =====================================================
        return UIResponse(
            state=state,
            # HIDE SETUP
            role_visible=False,
            interview_type_visible=False,
            company_visible=False,
            language_visible=False,
            start_button_visible=False,
            # HEADER
            page_title=page_title,
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
            submit_interactive=False,
            show_retry=buttons["show_retry"],
            show_next=buttons["show_next"],
            next_label=buttons.get("next_label") or "",
            submit_label=submit_label,
            # EDITORS
            written_editor_value=editor_value if is_written else "",
            coding_editor_value=editor_value if is_coding else "",
            database_editor_value=editor_value if is_database else "",
            written_editor_visible=is_written,
            coding_editor_visible=is_coding,
            database_editor_visible=is_database,
        )
