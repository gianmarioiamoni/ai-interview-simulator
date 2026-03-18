# app/ui/state_handlers.py

import os
from datetime import datetime

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_type import InterviewType
from domain.contracts.role import RoleType
from domain.contracts.question import QuestionType

from domain.events.answer_submitted_event import AnswerSubmittedEvent

from services.report_export_service import ReportExportService

from app.ui.sample_data_loader import load_sample_questions
from app.ui.ui_state import UIState
from app.ui.ui_response import UIResponse
from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.views.report_view import build_report_markdown
from app.ui.mappers.ui_state_mapper import UIStateMapper
from app.ui.presenters.evaluation_presenter import EvaluationPresenter

from app.ai.test_generation.ai_test_generator import AITestGenerator
from app.application.use_cases.evaluate_answer import EvaluateAnswerUseCase

from app.runtime.interview_runtime import (
    get_runtime_graph,
    get_runtime_evaluation_service,
)

export_service = ReportExportService()
test_generator = AITestGenerator()

MAX_ATTEMPTS = 3


# =========================================================
# INTERNAL HELPERS
# =========================================================


def _ensure_final_evaluation(state: InterviewState) -> InterviewState:
    # Ensure final_evaluation is populated.
    # Avoid duplication between next_question/export.

    if state.final_evaluation is None:

        evaluation_service = get_runtime_evaluation_service()

        state.final_evaluation = evaluation_service.evaluate(
            per_question_evaluations=state.evaluations_list,
            questions=state.questions,
            interview_type=state.interview_type,
            role=state.role.type,
        )

    return state


# =========================================================
# START INTERVIEW
# =========================================================


def start_interview(role: str, interview_type: str, company: str, language: str):

    role_type = RoleType[role.replace(" ", "_")]
    interview_type_enum = InterviewType[interview_type]

    questions = load_sample_questions(interview_type_enum.value)

    enriched_questions = []

    for q in questions:
        if q.type == QuestionType.CODING:
            hidden_tests = test_generator.generate_tests(q, num_tests=3)
            q = q.model_copy(update={"hidden_tests": hidden_tests})

        enriched_questions.append(q)

    state = InterviewState.create_initial(
        role_type=role_type,
        interview_type=interview_type_enum,
        company=company,
        language=language,
        questions=enriched_questions,
        interview_id="session-1",
    )

    graph = get_runtime_graph()
    state = graph.invoke(state)

    return build_ui_response_from_state(state)


# =========================================================
# SUBMIT ANSWER
# =========================================================

def submit_answer(state: InterviewState, user_answer: str):

    question = state.current_question

    event = AnswerSubmittedEvent(
        question_id=question.id,
        content=user_answer,
    )

    state = state.apply_event(event)

    from infrastructure.llm.llm_factory import get_llm

    llm = get_llm()
    use_case = EvaluateAnswerUseCase(llm)

    state = use_case.execute(state)

    return build_ui_response_from_state(state)


# =========================================================
# UI RESPONSE BUILDER
# =========================================================

def build_ui_response_from_state(state: InterviewState) -> UIResponse:

    session_dto = InterviewSessionDTO.from_state(state)
    ui_state = UIStateMapper.map_state(state)

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
    clarification_needed = False

    current_q = state.current_question

    if current_q and state.is_question_processed(current_q):

        result = state.get_result_for_question(current_q.id)

        if result and result.evaluation:

            presenter = EvaluationPresenter()

            vm = presenter.present(
                decision=result.evaluation,
                execution_results=[result.execution] if result.execution else [],
            )

            feedback_markdown = vm.feedback_markdown
            clarification_needed = vm.clarification_needed

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
        show_next=is_feedback and not clarification_needed,
        next_label="Generate Report" if state.is_last_question else "Next Question",
    )


# =========================================================
# RETRY
# =========================================================

def retry_answer(state: InterviewState):

    new_state = state.model_copy(deep=True)

    q = new_state.current_question

    if q:
        new_state.attempts_by_question[q.id] = (
            new_state.attempts_by_question.get(q.id, 0) + 1
        )
        new_state.reset_current_question()

    response = build_ui_response_from_state(new_state)
    response.ui_state = UIState.QUESTION

    return response


# =========================================================
# NEXT QUESTION
# =========================================================

def next_question(state: InterviewState):

    if state.is_last_question:

        state = _ensure_final_evaluation(state)

        response = build_ui_response_from_state(state)
        response.ui_state = UIState.REPORT

        return response.to_gradio_outputs()

    state.advance_question()

    graph = get_runtime_graph()
    state = graph.invoke(state)

    return build_ui_response_from_state(state).to_gradio_outputs()


# =========================================================
# NEW INTERVIEW
# =========================================================

def new_interview():

    return UIResponse(
        state=None,
        question_counter="",
        feedback="",
        written_text="",
        coding_text="",
        database_text="",
        written_visible=False,
        coding_visible=False,
        database_visible=False,
        ui_state=UIState.SETUP,
        final_feedback="",
        show_submit=False,
        show_retry=False,
        show_next=False,
    )


# =========================================================
# EXPORT
# =========================================================

def export_pdf(state: InterviewState) -> str:

    state = _ensure_final_evaluation(state)

    report = FinalReportDTO.from_state(state)

    os.makedirs("/mnt/data", exist_ok=True)

    path = f"/mnt/data/{state.interview_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

    export_service.export_pdf(report, path)

    return path


def export_json(state: InterviewState) -> str:

    state = _ensure_final_evaluation(state)

    report = FinalReportDTO.from_state(state)

    os.makedirs("/mnt/data", exist_ok=True)

    path = f"/mnt/data/{state.interview_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    export_service.export_json(report, path)

    return path
