# app/ui/builders/ui_response_builder.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType

from app.ui.ui_response import UIResponse
from app.ui.ui_state import UIState
from app.ui.state_machine.ui_state_machine import UIStateMachine

from app.ui.mappers.loader_mapper import map_loader_text
from app.ui.mappers.interview_area_mapper import InterviewAreaMapper

from app.ui.response.sections.display_section import DisplaySection
from app.ui.response.sections.feedback_section import FeedbackSection
from app.ui.response.sections.counter_section import CounterSection
from app.ui.response.config.button_mapper import ButtonMapper

from app.ui.components.loader.loader_renderer import render_loader

# 🔥 NEW IMPORTS (STEP 1)
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.views.report_view import build_report_markdown


MAX_ATTEMPTS = 3


class UIResponseBuilder:

    def build(self, state: InterviewState) -> UIResponse:

        ui_state = UIStateMachine.resolve(state)

        print(f"[DEBUG UI STATE] {ui_state}")
        print(f"[DEBUG FEEDBACK BUNDLE] {state.last_feedback_bundle is not None}")

        if ui_state == UIState.SETUP:
            return self._build_setup(state)

        if ui_state == UIState.QUESTION:
            return self._build_question_like(state, ui_state)

        if ui_state == UIState.FEEDBACK:
            return self._build_question_like(state, ui_state)

        if ui_state == UIState.REPORT:
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
    # QUESTION + FEEDBACK (UNCHANGED)
    # =====================================================
    def _build_question_like(
        self, state: InterviewState, ui_state: UIState
    ) -> UIResponse:

        if not state or not state.questions:
            return self._build_setup(state)

        question = state.current_question

        if question is None:
            return self._build_setup(state)

        is_written = question.is_written()
        is_coding = question.is_coding()
        is_database = question.is_database()

        is_feedback_mode = ui_state == UIState.FEEDBACK
        latest_answer = state.get_latest_answer_for_question(question.id)
        previous_value = latest_answer.content if latest_answer else ""

        attempts = state.get_attempt_for_question(question.id)
        can_retry = attempts < MAX_ATTEMPTS

        display = DisplaySection.build(state, question, ui_state, attempts > 0)
        feedback = FeedbackSection.build(state) if ui_state == UIState.FEEDBACK else ""
        counter = CounterSection.build(state, question, attempts, MAX_ATTEMPTS)
        buttons = ButtonMapper.map(state, ui_state, can_retry)

        loader_visible = state.current_step is not None
        loader_value = map_loader_text(state.current_step)

        if is_feedback_mode and previous_value:
            written_display = (
                f"<div><strong>Your previous answer:</strong><br>{previous_value}</div>"
                if is_written
                else ""
            )
            coding_display = display["coding_display"] if is_coding else ""
            database_display = display["database_display"] if is_database else ""
        else:
            written_display = display.get("written_display", "")
            coding_display = display.get("coding_display", "")
            database_display = display.get("database_display", "")

        area_label = InterviewAreaMapper.to_label(question.area)

        if is_feedback_mode:
            written_editor_value = ""
            coding_editor_value = ""
            database_editor_value = ""
        else:
            written_editor_value = ""
            coding_editor_value = "# Write your solution here" if is_coding else ""
            database_editor_value = (
                "-- Write your SQL query here" if is_database else ""
            )

        if is_coding:
            submit_label = "Run Code"
        elif is_database:
            submit_label = "Run Query"
        else:
            submit_label = "Submit Answer"

        return UIResponse(
            state=state,
            role_visible=False,
            interview_type_visible=False,
            company_visible=False,
            language_visible=False,
            start_button_visible=False,
            page_title=f"## {area_label}",
            question_counter=counter,
            feedback_markdown=feedback,
            written_display=written_display,
            coding_display=coding_display,
            database_display=database_display,
            written_visible=is_written,
            coding_visible=is_coding,
            database_visible=is_database,
            show_submit=buttons["show_submit"],
            submit_interactive=False,
            show_retry=buttons["show_retry"],
            show_next=buttons["show_next"],
            next_label=buttons.get("next_label") or "",
            submit_label=submit_label,
            written_editor_value=written_editor_value if is_written else "",
            coding_editor_value=coding_editor_value if is_coding else "",
            database_editor_value=database_editor_value if is_database else "",
            written_editor_visible=is_written and not is_feedback_mode,
            coding_editor_visible=is_coding and not is_feedback_mode,
            database_editor_visible=is_database and not is_feedback_mode,
            loader_visible=loader_visible,
            loader_value=loader_value,
        )

    # =====================================================
    # REPORT (🔥 FIX CORRETTO)
    # =====================================================
    def _build_report(self, state: InterviewState) -> UIResponse:

        final_eval = state.interview_evaluation

        if final_eval is None:
            return UIResponse(
                state=state,
                role_visible=False,
                interview_type_visible=False,
                company_visible=False,
                language_visible=False,
                start_button_visible=False,
                page_title="## Final Report",
                report_output="<i>No report available</i>",
            )

        # -----------------------------------------------------
        # 🔥 DTO (CRITICAL)
        # -----------------------------------------------------
        report_dto = FinalReportDTO.from_components(
            state=state,
            final_evaluation=final_eval,
        )

        # -----------------------------------------------------
        # 🔥 FULL RENDER (RADAR + ALL SECTIONS)
        # -----------------------------------------------------
        report_html = build_report_markdown(report_dto)

        # -----------------------------------------------------
        # RESPONSE
        # -----------------------------------------------------
        return UIResponse(
            state=state,
            role_visible=False,
            interview_type_visible=False,
            company_visible=False,
            language_visible=False,
            start_button_visible=False,
            page_title="## Final Report",
            report_output=report_html,
        )
