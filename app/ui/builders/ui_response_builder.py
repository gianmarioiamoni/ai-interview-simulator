# app/ui/builders/ui_response_builder.py

from domain.contracts.interview_state import InterviewState

from app.ui.ui_response import UIResponse
from app.ui.ui_state import UIState
from app.ui.state_machine.ui_state_machine import UIStateMachine

from app.ui.mappers.loader_mapper import map_loader_text
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
        counter = CounterSection.build(state, question, attempts, MAX_ATTEMPTS)
        buttons = ButtonMapper.map(state, ui_state, can_retry)

        loader_visible = state.current_step is not None
        loader_value = map_loader_text(state.current_step)

        is_processing = state.current_step is not None

        show_submit = buttons["show_submit"] and not is_processing

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

        submit_interactive = (
            buttons.get("show_submit_interactive", False)
            and not loader_visible
            and not is_feedback_mode
        )

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
            show_submit=show_submit,
            submit_interactive=submit_interactive,
            show_retry=buttons["show_retry"],
            show_next=buttons["show_next"],
            next_label=buttons.get("next_label") or "",
            written_editor_visible=is_written and not is_feedback_mode,
            coding_editor_visible=is_coding and not is_feedback_mode,
            database_editor_visible=is_database and not is_feedback_mode,
            loader_visible=loader_visible,
            loader_value=loader_value,
        )

    # =====================================================
    # REPORT
    # =====================================================
    def _build_report(self, state: InterviewState) -> UIResponse:

        final_eval = state.interview_evaluation

        loader_visible = state.current_step is not None
        loader_value = map_loader_text(state.current_step)

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
                report_section_visible=True,
                loader_visible=loader_visible,
                loader_value=loader_value,
            )

        report_dto = FinalReportDTO.from_components(
            state=state,
            final_evaluation=final_eval,
        )

        report_html = build_report_markdown(report_dto)

        return UIResponse(
            state=state,
            role_visible=False,
            interview_type_visible=False,
            company_visible=False,
            language_visible=False,
            start_button_visible=False,
            page_title="## Final Report",
            report_output=report_html,
            report_section_visible=True,
            show_submit=False,
            show_retry=False,
            show_next=False,
            written_visible=False,
            coding_visible=False,
            database_visible=False,
            loader_visible=loader_visible,
            loader_value=loader_value,
        )
