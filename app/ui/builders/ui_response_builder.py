# app/ui/builders/ui_response_builder.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType

from app.ui.ui_response import UIResponse
from app.ui.state_machine.ui_state_machine import UIStateMachine

from app.ui.mappers.loader_mapper import map_loader_text
from app.ui.mappers.interview_area_mapper import InterviewAreaMapper

from app.ui.response.sections.display_section import DisplaySection
from app.ui.response.sections.feedback_section import FeedbackSection
from app.ui.response.sections.counter_section import CounterSection
from app.ui.response.config.button_mapper import ButtonMapper


MAX_ATTEMPTS = 3


class UIResponseBuilder:

    def build(self, state: InterviewState) -> UIResponse:

        ui_state = UIStateMachine.resolve(state)

        if ui_state.name == "SETUP":
            return self._build_setup(state)

        if ui_state.name == "QUESTION":
            return self._build_question_like(state, mode="QUESTION")

        if ui_state.name == "FEEDBACK":
            return self._build_question_like(state, mode="FEEDBACK")

        if ui_state.name == "REPORT":
            return self._build_report(state)

        return self._build_setup(state)

    # =====================================================
    # SETUP
    # =====================================================
    def _build_setup(self, state: InterviewState) -> UIResponse:

        loader_visible = state.current_step is not None
        loader_value = map_loader_text(state.current_step)

        return UIResponse(
            state=state,
            role_visible=True,
            interview_type_visible=True,
            company_visible=True,
            language_visible=True,
            start_button_visible=True,
            page_title="## Configure Your Interview",
            loader_visible=True,
            loader_value="TEST VALUE"
        )

    # =====================================================
    # QUESTION + FEEDBACK (SHARED)
    # =====================================================
    def _build_question_like(self, state: InterviewState, mode: str) -> UIResponse:

        question = state.current_question
        if question is None:
            return self._build_setup(state)

        attempts = state.get_attempt_for_question(question.id)
        can_retry = attempts < MAX_ATTEMPTS

        display = DisplaySection.build(state, question, mode, attempts > 0)
        feedback = FeedbackSection.build(state) if mode == "FEEDBACK" else ""
        counter = CounterSection.build(state, question, attempts, MAX_ATTEMPTS)
        buttons = ButtonMapper.map(state, mode, can_retry)

        # -----------------------------------------------------
        # LOADER (UNIFICATO)
        # -----------------------------------------------------
        loader_visible = state.current_step is not None
        loader_value = map_loader_text(state.current_step)

        # -----------------------------------------------------
        # DISPLAY
        # -----------------------------------------------------
        written_display = f"<div>{display.get('written_display', '')}</div>"
        coding_display = display.get("coding_display", "")
        database_display = display.get("database_display", "")

        # -----------------------------------------------------
        # TYPE FLAGS
        # -----------------------------------------------------
        is_written = question.type == QuestionType.WRITTEN
        is_coding = question.type == QuestionType.CODING
        is_database = question.type == QuestionType.DATABASE

        # -----------------------------------------------------
        # TITLE
        # -----------------------------------------------------
        area_label = InterviewAreaMapper.to_label(question.area)

        # -----------------------------------------------------
        # EDITOR DEFAULTS
        # -----------------------------------------------------
        editor_value = ""
        if is_coding:
            editor_value = "# Write your solution here"
        elif is_database:
            editor_value = "-- Write your SQL query here"

        # -----------------------------------------------------
        # BUTTON LABEL
        # -----------------------------------------------------
        if is_coding:
            submit_label = "Run Code"
        elif is_database:
            submit_label = "Run Query"
        else:
            submit_label = "Submit Answer"

        # -----------------------------------------------------
        # FINAL UI RESPONSE
        # -----------------------------------------------------
        return UIResponse(
            state=state,
            # HIDE SETUP
            role_visible=False,
            interview_type_visible=False,
            company_visible=False,
            language_visible=False,
            start_button_visible=False,
            # HEADER
            page_title=f"## {area_label}",
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
            # LOADER
            loader_visible=loader_visible,
            loader_value=loader_value,
        )

    # =====================================================
    # REPORT
    # =====================================================
    def _build_report(self, state: InterviewState) -> UIResponse:

        return UIResponse(
            state=state,
            role_visible=False,
            interview_type_visible=False,
            company_visible=False,
            language_visible=False,
            start_button_visible=False,
            page_title="## Final Report",
            report_output="Report ready",
        )
