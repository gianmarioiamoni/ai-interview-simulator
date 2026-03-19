# ui/builders/ui_response_builder.py

from typing import TypedDict

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType

from app.ui.dto.question_dto import QuestionDTO
from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.views.report_view import build_report_markdown
from app.ui.presenters.result_presenter import ResultPresenter
from app.ui.ui_response import UIResponse
from app.ui.ui_state import UIState
from app.ui.state_machine.ui_state_machine import UIStateMachine


MAX_ATTEMPTS = 3

class DisplayFields(TypedDict):
    written_display: str
    coding_display: str
    database_display: str

class VisibilityFields(TypedDict):
    written_visible: bool
    coding_visible: bool
    database_visible: bool

class EditorVisibilityFields(TypedDict):
    written_editor_visible: bool
    coding_editor_visible: bool
    database_editor_visible: bool

class UIResponseBuilder:

    def __init__(self) -> None:
        self._presenter = ResultPresenter()

    # =========================================================
    # PUBLIC API
    # =========================================================

    def build(self, state: InterviewState) -> UIResponse:

        session_dto = InterviewSessionDTO.from_state(state)
        ui_state = UIStateMachine.resolve(state)

        if ui_state == UIState.REPORT:
            return self._build_report(state)

        if ui_state == UIState.COMPLETION:
            return self._build_completion(state)

        return self._build_question(state, session_dto, ui_state)

    # =========================================================
    # REPORT
    # =========================================================

    def _build_report(self, state: InterviewState) -> UIResponse:

        report = FinalReportDTO.from_state(state)
        report_md = build_report_markdown(report)

        return UIResponse(
            state=state,
            ui_state=UIState.REPORT,
            report_output=report_md,
            show_submit=False,
            show_retry=False,
            show_next=False,
        )

    # =========================================================
    # COMPLETION
    # =========================================================

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

        attempts = state.attempts_by_question.get(question.question_id, 0)
        can_retry = attempts < MAX_ATTEMPTS

        counter = self._build_counter(question, attempts)
        feedback = self._build_feedback(state)
        display = self._build_display(state, question, ui_state)

        visibility = self._build_visibility(question)
        editors = self._build_editor_visibility(question, ui_state)

        return UIResponse(
            state=state,
            question_counter=counter,
            feedback=feedback,
            ui_state=ui_state,
            show_submit=not self._is_feedback(ui_state),
            show_submit_interactive=not self._is_feedback(ui_state),
            show_retry=self._is_feedback(ui_state) and can_retry,
            show_next=self._is_feedback(ui_state),
            next_label="Generate Report" if state.is_last_question else "Next Question",
            **display,
            **visibility,
            **editors,
        )

    # =========================================================
    # SUB BUILDERS
    # =========================================================

    def _build_counter(self, question: QuestionDTO, attempts: int) -> str:

        return (
            f"### Interview Progress\n\n"
            f"Question {question.index} / {question.total}\n\n"
            f"Area: {question.area}\n\n"
            f"Attempts: {attempts} / {MAX_ATTEMPTS}"
        )

    # ---------------------------------------------------------

    def _build_feedback(self, state: InterviewState) -> str:

        current_q = state.current_question

        if not current_q or not state.is_question_processed(current_q):
            return ""

        result = state.get_result_for_question(current_q.id)

        if not result:
            return ""

        vm = self._presenter.present(result)

        return vm.feedback_markdown

    # ---------------------------------------------------------

    def _build_display(self, state: InterviewState, question: QuestionDTO, ui_state: UIState) -> DisplayFields:
        is_feedback = self._is_feedback(ui_state)
        last_answer = state.last_answer
        answer_content = last_answer.content if last_answer else ""
        text = answer_content if is_feedback else question.text
        prefix = "### Your Answer\n\n" if is_feedback else "### Question\n\n"
        display_text = prefix + text

        return {
            "written_display": display_text if question.type == QuestionType.WRITTEN else "",
            "coding_display": display_text if question.type == QuestionType.CODING else "",
            "database_display": display_text if question.type == QuestionType.DATABASE else "",
        }

    # ---------------------------------------------------------

    def _build_visibility(self, question: QuestionDTO) -> VisibilityFields:

        return {
            "written_visible": question.type == QuestionType.WRITTEN,
            "coding_visible": question.type == QuestionType.CODING,
            "database_visible": question.type == QuestionType.DATABASE,
        }

    # ---------------------------------------------------------

    def _build_editor_visibility(self, question: QuestionDTO, ui_state: UIState) -> EditorVisibilityFields:

        show_editor = not self._is_feedback(ui_state)

        return {
            "written_editor_visible": question.type == QuestionType.WRITTEN and show_editor,
            "coding_editor_visible": question.type == QuestionType.CODING and show_editor,
            "database_editor_visible": question.type == QuestionType.DATABASE and show_editor,
        }

    def _is_feedback(self, ui_state: UIState) -> bool:
        return ui_state == UIState.FEEDBACK
