# ui/builders/ui_response_builder.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType
from domain.contracts.test_execution_result import TestStatus, TestType

from app.ui.dto.question_dto import QuestionDTO
from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.views.report_view import build_report_markdown
from app.ui.presenters.result_presenter import ResultPresenter
from app.ui.ui_response import UIResponse
from app.ui.ui_state import UIState
from app.ui.state_machine.ui_state_machine import UIStateMachine
from app.ui.types.ui_fields import DisplayFields, VisibilityFields, EditorVisibilityFields, ButtonState


MAX_ATTEMPTS = 3


class UIResponseBuilder:

    def __init__(self) -> None:
        self._presenter = ResultPresenter()

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
    # SETUP
    # =========================================================

    def _build_setup(self, state: InterviewState) -> UIResponse:

        return UIResponse(
            state=state,
            ui_state=UIState.SETUP,
            show_submit=False,
            show_retry=False,
            show_next=False,
    )

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
        display = self._build_display(state, question, ui_state, error_hint)

        visibility = self._build_visibility(question)
        editors = self._build_editor_visibility(question, ui_state)

        buttons = self._build_buttons(state, ui_state, can_retry)

        # set previous question answer
        editor_value = editor_value or ""

        if state.last_answer and state.last_answer.question_id == question.question_id:
            editor_value = state.last_answer.content

        if not editor_value and question.type == QuestionType.CODING:
            editor_value = "# Write your solution here"
        
        # set error hint
        result = state.get_result_for_question(question.question_id)
        error_hint = self._build_error_hint(result.execution if result else None)

        return UIResponse(
            state=state,
            question_counter=counter,
            feedback=feedback,
            ui_state=ui_state,
            **buttons,
            **display,
            **visibility,
            **editors,
            # ---------------- EDITOR VALUES
            written_editor_value=editor_value if question.type == QuestionType.WRITTEN else "",
            coding_editor_value=editor_value if question.type == QuestionType.CODING else "",
            database_editor_value=editor_value if question.type == QuestionType.DATABASE else "",
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

    def _build_display(
        self,
        state: InterviewState,
        question: QuestionDTO,
        ui_state: UIState,
        error_hint: str,
    ) -> DisplayFields:
        is_feedback = self._is_feedback(ui_state)

        last_answer = state.last_answer
        answer_content = last_answer.content if last_answer else ""

        text = answer_content if is_feedback else question.text

        prefix = "### Your Answer\n\n" if is_feedback else "### Question\n\n"

        if error_hint:
            prefix += f"```\n{error_hint}\n```\n\n"
        
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

    def _build_buttons(
        self,
        state: InterviewState,
        ui_state: UIState,
        can_retry: bool,
    ) -> ButtonState:

        is_feedback = self._is_feedback(ui_state)

        return {
            "show_submit": not is_feedback,
            "show_submit_interactive": not is_feedback,
            "show_retry": is_feedback and can_retry,
            "show_next": is_feedback,
            "next_label": "Generate Report" if state.is_last_question else "Next Question",
    }


    def _build_error_hint(self, execution) -> str:
        if not execution or not execution.test_results:
            return ""

        failed = [
            t for t in execution.test_results
            if t.type == TestType.VISIBLE and t.status != TestStatus.PASSED
        ]

        if not failed:
            failed = [
                t for t in execution.test_results
                if t.status != TestStatus.PASSED
            ]

        if not failed:
            return ""

        t = failed[0]

        if t.status == TestStatus.ERROR:
            return f"**⚠️ Runtime error with input {t.args}: {t.error}**"

        
        return (
            "⚠️ Failing test:\n"
            f"Input: {t.args}\n"
            f"Expected: {repr(t.expected)}\n"
            f"Actual: {repr(t.actual)}"
        )
