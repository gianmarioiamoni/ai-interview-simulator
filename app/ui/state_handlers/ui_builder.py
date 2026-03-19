# app/ui/state_handlers/ui_builder.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType

from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.final_report_dto import FinalReportDTO

from app.ui.views.report_view import build_report_markdown
from app.ui.presenters.result_presenter import ResultPresenter

from app.ui.ui_response import UIResponse
from app.ui.ui_state import UIState
from app.ui.state_machine.ui_state_machine import UIStateMachine


MAX_ATTEMPTS = 3

QUESTION_TYPES = list(QuestionType)

# =========================================================
# ENTRY POINT
# =========================================================

def build_ui_response_from_state(state: InterviewState) -> UIResponse:

    session_dto = InterviewSessionDTO.from_state(state)
    ui_state = UIStateMachine.resolve(state)

    if ui_state == UIState.REPORT:
        return _build_report_response(state)

    if ui_state == UIState.COMPLETION:
        return _build_completion_response(state)

    return _build_question_response(state, session_dto, ui_state)


# =========================================================
# REPORT
# =========================================================

def _build_report_response(state: InterviewState) -> UIResponse:

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

def _build_completion_response(state: InterviewState) -> UIResponse:

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


def _build_question_response(
    state: InterviewState,
    session_dto: InterviewSessionDTO,
    ui_state: UIState,
) -> UIResponse:

    question = session_dto.current_question

    if question is None:
        raise RuntimeError("UI attempted to render question but none exists")

    attempts = state.attempts_by_question.get(question.question_id, 0)
    can_retry = attempts < MAX_ATTEMPTS

    counter = _build_counter(question, attempts)

    feedback_markdown = _build_evaluation(state)

    display_text, show_editor = _build_display(state, question, ui_state)

    # Dynamic mapping
    qt = question.type
    display_fields = _build_display_fields(qt, display_text)
    visibility_fields = _build_visibility_fields(qt)
    editor_fields = _build_editor_fields(qt, show_editor)

    return UIResponse(
        state=state,
        question_counter=counter,
        feedback=feedback_markdown,
        ui_state=ui_state,
        show_submit=not _is_feedback(ui_state),
        show_submit_interactive=not _is_feedback(ui_state),
        show_retry=_is_feedback(ui_state) and can_retry,
        show_next=_is_feedback(ui_state),
        next_label="Generate Report" if state.is_last_question else "Next Question",
        **display_fields,
        **visibility_fields,
        **editor_fields,
    )


# =========================================================
# SUB BUILDERS
# =========================================================

def _build_counter(question, attempts: int) -> str:

    return (
        f"### Interview Progress\n\n"
        f"Question {question.index} / {question.total}\n\n"
        f"Area: {question.area}\n\n"
        f"Attempts: {attempts} / {MAX_ATTEMPTS}"
    )


def _build_evaluation(state: InterviewState) -> str:

    current_q = state.current_question

    if not current_q or not state.is_question_processed(current_q):
        return ""

    result = state.get_result_for_question(current_q.id)

    if not result:
        return ""

    presenter = ResultPresenter()

    # Written question
    if result.evaluation:
        vm = presenter.present(result)
        return vm.feedback_markdown

    # Coding / Database question
    if result.execution:
        vm = presenter.present(
            evaluation=None,
            execution_results=[result.execution],
        )
        return vm.feedback_markdown

    return ""


def _build_display(state, question, ui_state):

    is_feedback = _is_feedback(ui_state)

    last_answer = state.last_answer
    answer_content = last_answer.content if last_answer else ""

    display_text = answer_content if is_feedback else question.text

    label_prefix = "### Your Answer\n\n" if is_feedback else "### Question\n\n"

    return label_prefix + display_text, not is_feedback


def _is_feedback(ui_state: UIState) -> bool:
    return ui_state == UIState.FEEDBACK

# ------------------------------------------------------------
# DISPLAY FIELDS
# ------------------------------------------------------------

def _build_display_fields(question_type: QuestionType, display_text: str):

    return {
        f"{qt.value}_display": display_text if qt == question_type else ""
        for qt in QUESTION_TYPES
    }


def _build_visibility_fields(question_type: QuestionType):

    return {f"{qt.value}_visible": qt == question_type for qt in QUESTION_TYPES}


def _build_editor_fields(question_type: QuestionType, show_editor: bool):

    return {
        f"{qt.value}_editor_visible": (qt == question_type and show_editor)
        for qt in QUESTION_TYPES
    }
