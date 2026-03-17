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
from app.ui.handlers.report_handler import view_report_handler
from app.ui.views.report_view import build_report_markdown

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

    from app.ui.mappers.ui_state_mapper import UIStateMapper
    from app.ui.dto.final_report_dto import FinalReportDTO
    from app.ui.views.report_view import build_report_markdown

    session_dto = InterviewSessionDTO.from_state(state)

    feedback = ""
    score = None
    execution_error = None
    test_results_lines = []
    execution_status = ""

    # ---------------------------------------------------------
    # RESULT (current question)
    # ---------------------------------------------------------

    result = None
    current_q = state.current_question

    if current_q and state.is_question_processed(current_q):

        result = state.get_result_for_question(current_q.id)

        if result:

            # -------------------------
            # Evaluation
            # -------------------------

            if result.evaluation:
                feedback = result.evaluation.feedback
                score = getattr(result.evaluation, "score", None)

            # -------------------------
            # Execution
            # -------------------------

            if result.execution:

                passed = result.execution.passed_tests
                total = result.execution.total_tests

                if passed is not None and total is not None:
                    test_results_lines.append(f"✔ Passed: {passed} / {total}")

                execution_status = (
                    "PASSED" if result.execution.success else "FAILED TESTS"
                )

                if result.execution.error and not result.execution.success:
                    execution_error = result.execution.error

    # ---------------------------------------------------------
    # UI STATE
    # ---------------------------------------------------------

    ui_state = UIStateMapper.map_state(state)

    # =========================================================
    # REPORT STATE
    # =========================================================

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
            ui_state=UIState.REPORT,
            report_output=report_md,
            show_submit=False,
            show_retry=False,
            show_next=False,
        )

    # =========================================================
    # COMPLETION STATE
    # =========================================================

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
            ui_state=UIState.COMPLETION,
            show_submit=False,
            show_retry=False,
            show_next=False,
        )

    # =========================================================
    # QUESTION / FEEDBACK STATE
    # =========================================================

    question = session_dto.current_question

    if question is None:
        raise RuntimeError("UI attempted to render question but none exists")

    attempts = state.attempts_by_question.get(question.question_id, 0)
    can_retry = attempts < MAX_ATTEMPTS

    # ---------------------------------------------------------
    # COUNTER
    # ---------------------------------------------------------

    counter = (
        f"### Interview Progress\n\n"
        f"Question {question.index} / {question.total}\n\n"
        f"Area: {question.area}\n\n"
        f"Attempts: {attempts} / {MAX_ATTEMPTS}"
    )

    # ---------------------------------------------------------
    # EVALUATION PANEL
    # ---------------------------------------------------------

    evaluation_sections = []

    if score is not None:
        evaluation_sections.append(f"**Score:** {score} / 100")

    if feedback:
        evaluation_sections.append(f"**Feedback:**\n\n{feedback}")

    if test_results_lines:
        evaluation_sections.append(f"**Execution Results**\n\n{test_results_lines[0]}")

    if execution_status:
        evaluation_sections.append(f"**Execution status:** {execution_status}")

    if execution_error:
        evaluation_sections.append(f"⚠ **Execution error:** {execution_error}")

    if not can_retry:
        evaluation_sections.append("⚠ **Maximum attempts reached.**")

    feedback_markdown = ""
    if evaluation_sections:
        feedback_markdown = "### Evaluation\n\n" + "\n\n".join(evaluation_sections)

    # ---------------------------------------------------------
    # DISPLAY LOGIC (KEY STEP)
    # ---------------------------------------------------------

    is_feedback = ui_state == UIState.FEEDBACK

    last_answer = state.last_answer
    answer_content = last_answer.content if last_answer else ""

    display_text = answer_content if is_feedback else question.text

    label_prefix = "### Your Answer\n\n" if is_feedback else "### Question\n\n"

    display_text = label_prefix + display_text

    # ---------------------------------------------------------
    # EDITOR VISIBILITY
    # ---------------------------------------------------------

    show_editor = not is_feedback

    # ---------------------------------------------------------
    # RETURN
    # ---------------------------------------------------------

    return UIResponse(
        state=state,
        question_counter=counter,
        feedback=feedback_markdown,
        # DISPLAY (sempre visibile)
        written_display=display_text,
        coding_display=display_text,
        database_display=display_text,
        # EDITOR (solo QUESTION)
        written_visible=question.question_type == "written" and show_editor,
        coding_visible=question.question_type == "coding" and show_editor,
        database_visible=question.question_type == "database" and show_editor,
        ui_state=ui_state,
        show_submit=not is_feedback,
        show_submit_interactive=not is_feedback,
        show_retry=is_feedback and can_retry,
        show_next=is_feedback,
        next_label="Generate Report" if state.is_last_question else "Next Question",
    )


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

    evaluation_service = get_runtime_evaluation_service()

    if state.final_evaluation is None:

        final_eval = evaluation_service.evaluate(
            per_question_evaluations=state.evaluations_list,
            questions=state.questions,
            interview_type=state.interview_type,
            role=state.role.type,
        )

        state.final_evaluation = final_eval

    report = FinalReportDTO.from_state(state)

    os.makedirs("/mnt/data", exist_ok=True)

    path = f"/mnt/data/{state.interview_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

    export_service.export_pdf(report, path)

    return path

def export_json(state: InterviewState) -> str:

    evaluation_service = get_runtime_evaluation_service()

    if state.final_evaluation is None:

        final_eval = evaluation_service.evaluate(
            per_question_evaluations=state.evaluations_list,
            questions=state.questions,
            interview_type=state.interview_type,
            role=state.role.type,
        )

        state.final_evaluation = final_eval

    report = FinalReportDTO.from_state(state)

    os.makedirs("/mnt/data", exist_ok=True)

    path = f"/mnt/data/{state.interview_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    export_service.export_json(report, path)

    return path
