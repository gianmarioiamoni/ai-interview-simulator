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

from app.ui.components.loader.loader_renderer import render_loader


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
        progress = getattr(state, "current_progress", 0)
        setup_inputs_interactive = not loader_visible

        return UIResponse(
            state=state,
            role_visible=True,
            interview_type_visible=True,
            company_visible=True,
            language_visible=True,
            start_button_visible=True,
            page_title="## Configure Your Interview",
            loader_visible=loader_visible,
            loader_value=loader_value,
            current_progress=progress,
            setup_inputs_interactive=setup_inputs_interactive,
        )

    # =====================================================
    # QUESTION + FEEDBACK (SHARED)
    # =====================================================
    def _build_question_like(self, state: InterviewState, mode: str) -> UIResponse:

        is_feedback_mode = mode == "FEEDBACK"
        latest_answer = state.get_latest_answer_for_question(question.id)
        previous_value = latest_answer.content if latest_answer else ""

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
        if is_feedback_mode and previous_value:

            written_display = f"<div><strong>Your previous answer:</strong><br>{previous_value}</div>" if question.is_written() else ""
            coding_display = previous_value if is_coding else ""
            database_display = previous_value if is_database else ""

        else:
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
        # EDITOR VALUE
        # -----------------------------------------------------
        if is_feedback_mode:
            written_editor_value = "" if is_written else ""
            coding_editor_value = "" if is_coding else ""
            database_editor_value = "" if is_database else ""
        else:
            written_editor_value = "" if is_written else ""
            coding_editor_value = "# Write your solution here" if is_coding else ""
            database_editor_value = "-- Write your SQL query here" if is_database else ""
        
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
            written_editor_value=written_editor_value if is_written else "",
            coding_editor_value=coding_editor_value if is_coding else "",
            database_editor_value=database_editor_value if is_database else "",
            written_editor_visible=is_written and not is_feedback_mode,
            coding_editor_visible=is_coding and not is_feedback_mode,
            database_editor_visible=is_database and not is_feedback_mode,
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
