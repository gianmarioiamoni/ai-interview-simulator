# app/ui/builders/ui_response_builder.py

import html
from domain.contracts.interview_state import InterviewState
from domain.contracts.shared.action_type import ActionType

from app.ui.ui_response import UIResponse
from app.ui.ui_state import UIState
from app.ui.state_machine.ui_state_machine import UIStateMachine

from app.ui.mappers.loader_mapper import map_loader_text, map_loader_progress
from app.ui.mappers.interview_area_mapper import InterviewAreaMapper

from app.ui.response.sections.display_section import DisplaySection
from app.ui.response.sections.feedback_section import FeedbackSection
from app.ui.response.sections.counter_section import CounterSection
from app.ui.response.config.button_mapper import ButtonMapper

from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.views.report_view import build_report_markdown

MAX_ATTEMPTS = 3


class UIResponseBuilder:

    def build(self, state: InterviewState) -> UIResponse:

        ui_state = UIStateMachine.resolve(state)

        # ---------------------------------------------------------
        if ui_state == UIState.SETUP:
            return self._build_setup(state)

        if ui_state == UIState.PROCESSING:
            return self._build_processing(state)

        if ui_state == UIState.QUESTION:
            return self._build_question_like(state, ui_state)

        if ui_state == UIState.FEEDBACK:
            return self._build_question_like(state, ui_state)

        if ui_state == UIState.REPORT:
            return self._build_report(state)

        if ui_state == UIState.COMPLETION:
            return self._build_completion(state)

        return self._build_setup(state)

    # =====================================================
    # SETUP
    # =====================================================
    def _build_setup(self, state: InterviewState) -> UIResponse:

        loader_visible = state.current_step is not None
        loader_value = map_loader_text(state.current_step)
        progress = map_loader_progress(state.current_step)

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
        )

    # =====================================================
    # PROCESSING (LOADER STATE)
    # =====================================================
    def _build_processing(self, state: InterviewState) -> UIResponse:

        question = state.current_question

        # set page title based on intent
        is_report_processing = state.intent == ActionType.GENERATE_REPORT

        area_label = (
            "Generating Final Interview Evaluation" 
            if is_report_processing 
            else InterviewAreaMapper.to_label(question.area) if question else "Processing..."
        )

        loader_value = map_loader_text(state.current_step)
        progress = map_loader_progress(state.current_step)

        return UIResponse(
            state=state,
            role_visible=False,
            role_custom_name_visible=False,
            interview_type_visible=False,
            seniority_visible=False,
            interview_length_visible=False,
            company_visible=False,
            language_visible=False,
            start_button_visible=False,
            page_title=f"## {area_label}",
            feedback_markdown="",
            written_display="",
            coding_display="",
            database_display="",
            written_visible=False,
            coding_visible=False,
            database_visible=False,
            show_submit=True,
            submit_interactive=False,
            show_retry=False,
            show_next=False,
            written_editor_visible=False,
            coding_editor_visible=False,
            database_editor_visible=False,
            loader_visible=True,
            loader_value=loader_value,
            current_progress=progress,
        )

    # =====================================================
    # QUESTION + FEEDBACK
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
        feedback = FeedbackSection.build(state) if is_feedback_mode else ""
        display_attempt = attempts if is_feedback_mode else (attempts + 1)
        counter = CounterSection.build(state, question, display_attempt, MAX_ATTEMPTS)
        buttons = ButtonMapper.map(state, ui_state, can_retry)

        area_label = InterviewAreaMapper.to_label(question.area)

        # ---------------------------------------------------------
        # LOADER LOGIC (STATE-DRIVEN)
        # ---------------------------------------------------------
        loader_visible = state.is_processing
        loader_value = map_loader_text(state.current_step)
        progress = map_loader_progress(state.current_step)

        show_submit = buttons["show_submit"]

        # ---------------------------------------------------------
        # DISPLAY PREVIOUS ANSWER (FORMATTED)
        # ---------------------------------------------------------
        if is_feedback_mode and previous_value:
            formatted_answer = html.escape(previous_value).replace("\n", "<br>")

            written_display = (
                f"<div><strong>Your previous answer:</strong><br>{formatted_answer}</div>"
                if is_written
                else ""
            )
            coding_display = display["coding_display"] if is_coding else ""
            database_display = display["database_display"] if is_database else ""
        else:
            written_display = display.get("written_display", "")
            coding_display = display.get("coding_display", "")
            database_display = display.get("database_display", "")

        # ---------------------------------------------------------
        # SUBMIT ENABLED ONLY WHEN READY
        # ---------------------------------------------------------
        submit_interactive = (
            buttons.get("show_submit_interactive", False)
            and not state.is_processing
            and not is_feedback_mode
            and state.awaiting_user_input
        )

        # ---------------------------------------------------------
        # PRE-FILL EDITORS ON RETRY (QUESTION mode with prior answer)
        # ---------------------------------------------------------
        editor_prefill = previous_value if (not is_feedback_mode and previous_value) else ""

        return UIResponse(
            state=state,
            role_visible=False,
            role_custom_name_visible=False,
            interview_type_visible=False,
            seniority_visible=False,
            interview_length_visible=False,
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
            show_submit=show_submit,
            submit_interactive=submit_interactive,
            show_retry=buttons["show_retry"],
            retry_label=buttons.get("retry_label") or "",
            show_next=buttons["show_next"],
            next_label=buttons.get("next_label") or "",
            written_editor_visible=is_written and not is_feedback_mode,
            coding_editor_visible=is_coding and not is_feedback_mode,
            database_editor_visible=is_database and not is_feedback_mode,
            written_editor_value=editor_prefill if is_written else "",
            coding_editor_value=editor_prefill if is_coding else "",
            database_editor_value=editor_prefill if is_database else "",
            loader_visible=loader_visible,
            loader_value=loader_value,
            current_progress=progress,
        )

    # =====================================================
    # COMPLETION (interview done, report not yet generated)
    # =====================================================
    def _build_completion(self, state: InterviewState) -> UIResponse:

        loader_value = map_loader_text(state.current_step)
        progress = map_loader_progress(state.current_step)

        return UIResponse(
            state=state,
            role_visible=False,
            role_custom_name_visible=False,
            interview_type_visible=False,
            seniority_visible=False,
            interview_length_visible=False,
            company_visible=False,
            language_visible=False,
            start_button_visible=False,
            page_title="## Interview Complete",
            report_output="<i>Generating your final report, please wait…</i>",
            report_section_visible=True,
            pdf_download_btn_visible=False,
            json_download_btn_visible=False,
            show_submit=False,
            show_retry=False,
            show_next=False,
            written_visible=False,
            coding_visible=False,
            database_visible=False,
            loader_visible=state.is_processing,
            loader_value=loader_value,
            current_progress=progress,
        )

    # =====================================================
    # REPORT
    # =====================================================
    def _build_report(self, state: InterviewState) -> UIResponse:

        final_eval = state.interview_evaluation

        # loader_visible = state.current_step is not None
        loader_visible = False
        loader_value = map_loader_text(state.current_step)
        progress = map_loader_progress(state.current_step)

        if final_eval is None:
            return UIResponse(
                state=state,
                role_visible=False,
                role_custom_name_visible=False,
                interview_type_visible=False,
                seniority_visible=False,
                interview_length_visible=False,
                company_visible=False,
                language_visible=False,
                start_button_visible=False,
                page_title="## Final Report",
                report_output="<i>No report available</i>",
                report_section_visible=True,
                pdf_download_btn_visible=False,
                json_download_btn_visible=False,
                loader_visible=loader_visible,
                loader_value=loader_value,
                current_progress=progress,
            )

        report_dto = FinalReportDTO.from_components(
            state=state,
            final_evaluation=final_eval,
        )

        report_html = build_report_markdown(report_dto)

        return UIResponse(
            state=state,
            role_visible=False,
            role_custom_name_visible=False,
            interview_type_visible=False,
            seniority_visible=False,
            interview_length_visible=False,
            company_visible=False,
            language_visible=False,
            start_button_visible=False,
            page_title="## Final Report",
            report_output=report_html,
            report_section_visible=True,
            pdf_download_btn_visible=True,
            json_download_btn_visible=True,
            show_submit=False,
            show_retry=False,
            show_next=False,
            written_visible=False,
            coding_visible=False,
            database_visible=False,
            loader_visible=loader_visible,
            loader_value=loader_value,
            current_progress=progress,
        )
