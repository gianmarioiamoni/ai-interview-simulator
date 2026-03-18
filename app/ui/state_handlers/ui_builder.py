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


def build_ui_response_from_state(state: InterviewState) -> UIResponse:

    session_dto = InterviewSessionDTO.from_state(state)
    ui_state = UIStateMachine.resolve(state)

    # ---------------- REPORT ----------------
    if ui_state == UIState.REPORT:

        report = FinalReportDTO.from_state(state)
        report_md = build_report_markdown(report)

        return UIResponse(
            state=state,
            question_counter="",
            feedback="",
            written_display="",
            coding_display="",
            database_display="",
            written_visible=False,
            coding_visible=False,
            database_visible=False,
            written_editor_visible=False,
            coding_editor_visible=False,
            database_editor_visible=False,
            ui_state=UIState.REPORT,
            report_output=report_md,
            show_submit=False,
            show_retry=False,
            show_next=False,
        )

    # ---------------- COMPLETION ----------------
    if ui_state == UIState.COMPLETION:

        return UIResponse(
            state=state,
            question_counter="",
            feedback="",
            written_display="",
            coding_display="",
            database_display="",
            written_visible=False,
            coding_visible=False,
            database_visible=False,
            written_editor_visible=False,
            coding_editor_visible=False,
            database_editor_visible=False,
            ui_state=UIState.COMPLETION,
            show_submit=False,
            show_retry=False,
            show_next=False,
        )

    # ---------------- QUESTION ----------------

    question = session_dto.current_question

    if question is None:
        raise RuntimeError("UI attempted to render question but none exists")

    attempts = state.attempts_by_question.get(question.question_id, 0)
    can_retry = attempts < MAX_ATTEMPTS

    counter = (
        f"### Interview Progress\n\n"
        f"Question {question.index} / {question.total}\n\n"
        f"Area: {question.area}\n\n"
        f"Attempts: {attempts} / {MAX_ATTEMPTS}"
    )

    # ---------------- EVALUATION ----------------

    feedback_markdown = ""

    current_q = state.current_question

    if current_q and state.is_question_processed(current_q):

        result = state.get_result_for_question(current_q.id)

        if result and result.evaluation:

            presenter = EvaluationPresenter()

            vm = presenter.present(
                evaluation=result.evaluation,
                execution_results=[result.execution] if result.execution else [],
            )

            feedback_markdown = vm.feedback_markdown

    # ---------------- DISPLAY ----------------

    is_feedback = ui_state == UIState.FEEDBACK

    last_answer = state.last_answer
    answer_content = last_answer.content if last_answer else ""

    display_text = answer_content if is_feedback else question.text

    label_prefix = "### Your Answer\n\n" if is_feedback else "### Question\n\n"
    display_text = label_prefix + display_text

    show_editor = not is_feedback

    written_display = display_text if question.question_type == "written" else ""
    coding_display = display_text if question.question_type == "coding" else ""
    database_display = display_text if question.question_type == "database" else ""

    return UIResponse(
        state=state,
        question_counter=counter,
        feedback=feedback_markdown,
        written_display=written_display,
        coding_display=coding_display,
        database_display=database_display,
        written_visible=question.question_type == "written",
        coding_visible=question.question_type == "coding",
        database_visible=question.question_type == "database",
        written_editor_visible=question.question_type == "written" and show_editor,
        coding_editor_visible=question.question_type == "coding" and show_editor,
        database_editor_visible=question.question_type == "database" and show_editor,
        ui_state=ui_state,
        show_submit=not is_feedback,
        show_submit_interactive=not is_feedback,
        show_retry=is_feedback and can_retry,
        show_next=is_feedback,
        next_label="Generate Report" if state.is_last_question else "Next Question",
    )
