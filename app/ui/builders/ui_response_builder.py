# app/ui/builders/ui_response_builder.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.feedback.quality import Quality
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

from app.ui.response.config.visibility_mapper import VisibilityMapper
from app.ui.response.config.editor_mapper import EditorMapper
from app.ui.response.config.button_mapper import ButtonMapper

MAX_ATTEMPTS = 3


class UIResponseBuilder:

    # =========================================================
    # PUBLIC API
    # =========================================================

    def build(self, state: InterviewState) -> UIResponse:

        session_dto = InterviewSessionDTO.from_state(state)
        ui_state = UIStateMachine.resolve(state)

        if ui_state == UIState.SETUP:
            return self._build_setup(state)

        if ui_state == UIState.REPORT:
            return self._build_report(state)

        if ui_state == UIState.COMPLETION:
            return self._build_completion(state)

        if ui_state in [UIState.QUESTION, UIState.FEEDBACK]:
            return self._build_question(state, session_dto, ui_state)

        raise RuntimeError(f"Unsupported UI state: {ui_state}")

    # =========================================================
    # STATIC STATES
    # =========================================================

    def _build_setup(self, state: InterviewState) -> UIResponse:
        return UIResponse(
            state=state,
            ui_state=UIState.SETUP,
            show_submit=False,
            show_retry=False,
            show_next=False,
        )

    def _build_report(self, state: InterviewState) -> UIResponse:

        mapper = InterviewStateMapper()
        report = mapper.to_final_report_dto(state)
        report_md = build_report_markdown(report)

        return UIResponse(
            state=state,
            ui_state=UIState.REPORT,
            report_output=report_md,
            show_submit=False,
            show_retry=False,
            show_next=False,
        )

    def _build_completion(self, state: InterviewState) -> UIResponse:
        return UIResponse(
            state=state,
            ui_state=UIState.COMPLETION,
            show_submit=False,
            show_retry=False,
            show_next=False,
        )

    # =========================================================
    # QUESTION / FEEDBACK
    # =========================================================

    def _build_question(
        self,
        state: InterviewState,
        session_dto: InterviewSessionDTO,
        ui_state: UIState,
    ) -> UIResponse:

        question = session_dto.current_question

        if question is None:
            raise RuntimeError("UI attempted to render question but none exists")

        attempts = state.get_attempt_for_question(question.question_id)
        has_previous_answer = attempts > 0
        can_retry = attempts < MAX_ATTEMPTS

        last_answer = state.get_latest_answer_for_question(question.question_id)

        editor_value = ""

        if last_answer and last_answer.question_id == question.question_id:
            editor_value = last_answer.content

        if not editor_value and question.type == QuestionType.CODING:
            editor_value = "# Write your solution here"

        # -----------------------------------------------------
        # FEEDBACK FIRST (important)
        # -----------------------------------------------------

        feedback_markdown = FeedbackSection.build(state)
        feedback_bundle = getattr(state, "last_feedback_bundle", None)

        if feedback_bundle:
            print("QUALITY DEBUG:", feedback_bundle.overall_quality)

        # -----------------------------------------------------
        # OTHER SECTIONS
        # -----------------------------------------------------

        # error_hint = ErrorHintBuilder.build(
        #     state,
        #     question,
        #     has_previous_answer,
        #     ui_state,
        # )

        display = DisplaySection.build(
            state,
            question,
            ui_state,
            has_previous_answer,
        )

        counter = CounterSection.build(question, attempts, MAX_ATTEMPTS)

        # -----------------------------------------------------
        # CONFIG
        # -----------------------------------------------------

        visibility = VisibilityMapper.map(question)
        editors = EditorMapper.map(question, ui_state)
        buttons = ButtonMapper.map(state, ui_state, can_retry)

        # -----------------------------------------------------
        # RESPONSE
        # -----------------------------------------------------

        return UIResponse(
            state=state,
            question_counter=counter,
            feedback_markdown=feedback_markdown,
            feedback_quality = feedback_bundle.overall_quality if feedback_bundle else None,
            ui_state=ui_state,
            **buttons,
            **display,
            **visibility,
            **editors,
            written_editor_value=(
                editor_value if question.type == QuestionType.WRITTEN else ""
            ),
            coding_editor_value=(
                editor_value if question.type == QuestionType.CODING else ""
            ),
            database_editor_value=(
                editor_value if question.type == QuestionType.DATABASE else ""
            ),
        )
