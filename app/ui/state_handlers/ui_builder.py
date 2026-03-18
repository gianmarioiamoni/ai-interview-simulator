# app/ui/state_handlers/ui_builder.py

from domain.contracts.interview_state import InterviewState

from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.final_report_dto import FinalReportDTO

from app.ui.views.report_view import build_report_markdown
from app.ui.presenters.evaluation_presenter import EvaluationPresenter

from app.ui.ui_response import UIResponse
from app.ui.ui_state import UIState
from app.ui.state_machine.ui_state_machine import UIStateMachine


MAX_ATTEMPTS = 3


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

    return UIResponse(
        state=state,
        question_counter=counter,
        feedback=feedback_markdown,
        written_display=display_text if question.question_type == "written" else "",
        coding_display=display_text if question.question_type == "coding" else "",
        database_display=display_text if question.question_type == "database" else "",
        written_visible=question.question_type == "written",
        coding_visible=question.question_type == "coding",
        database_visible=question.question_type == "database",
        written_editor_visible=question.question_type == "written" and show_editor,
        coding_editor_visible=question.question_type == "coding" and show_editor,
        database_editor_visible=question.question_type == "database" and show_editor,
        ui_state=ui_state,
        show_submit=not _is_feedback(ui_state),
        show_submit_interactive=not _is_feedback(ui_state),
        show_retry=_is_feedback(ui_state) and can_retry,
        show_next=_is_feedback(ui_state),
        next_label="Generate Report" if state.is_last_question else "Next Question",
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

    if not result or not result.evaluation:
        return ""

    presenter = EvaluationPresenter()

    vm = presenter.present(
        evaluation=result.evaluation,
        execution_results=[result.execution] if result.execution else [],
    )

    return vm.feedback_markdown


def _build_display(state, question, ui_state):

    is_feedback = _is_feedback(ui_state)

    last_answer = state.last_answer
    answer_content = last_answer.content if last_answer else ""

    display_text = answer_content if is_feedback else question.text

    label_prefix = "### Your Answer\n\n" if is_feedback else "### Question\n\n"

    return label_prefix + display_text, not is_feedback


def _is_feedback(ui_state: UIState) -> bool:
    return ui_state == UIState.FEEDBACK
