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

def start_interview(
    role: str,
    interview_type: str,
    company: str,
    language: str,
):

    role_type = RoleType[role.replace(" ", "_")]
    interview_type_enum = InterviewType[interview_type]

    questions = load_sample_questions(interview_type_enum.value)

    enriched_questions = []

    for q in questions:

        if q.type == QuestionType.CODING:

            hidden_tests = test_generator.generate_tests(
                q,
                num_tests=3,
            )

            q = q.model_copy(update={"hidden_tests": hidden_tests})

        enriched_questions.append(q)

    questions = enriched_questions

    state = InterviewState.create_initial(
        role_type=role_type,
        interview_type=interview_type_enum,
        company=company,
        language=language,
        questions=questions,
        interview_id="session-1",
    )

    graph = get_runtime_graph()
    state = graph.invoke(state)

    return build_ui_response_from_state(state)


# =========================================================
# GENERIC ANSWER SUBMIT
# =========================================================

def submit_answer(state: InterviewState, user_answer: str):

    question = state.current_question

    event = AnswerSubmittedEvent(
        question_id=question.id,
        content=user_answer,
    )

    state = state.apply_event(event)

    # ---------------------------------------------------------
    # Run only answer evaluation (NOT the full graph)
    # ---------------------------------------------------------

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

    session_dto = InterviewSessionDTO.from_state(state)

    feedback = ""
    score = None
    execution_error = None
    test_results_lines = []
    execution_status = ""

    # ---------------------------------------------------------
    # Retrieve result for the current question (only if processed)
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

                if hasattr(result.evaluation, "score"):
                    score = result.evaluation.score

            # -------------------------
            # Execution results
            # -------------------------

            if result.execution:

                if (
                    hasattr(result.execution, "test_results")
                    and result.execution.test_results
                ):

                    for test in result.execution.test_results:

                        name = getattr(test, "name", "test")
                        passed = getattr(test, "passed", False)

                        icon = "✔" if passed else "✘"

                        test_results_lines.append(f"{icon} {name}")

                if result.execution.success:
                    execution_status = "PASSED"
                else:
                    execution_status = "FAILED TESTS"

                if result.execution.error and not result.execution.success:

                    execution_error = result.execution.error

    # ---------------------------------------------------------
    # Determine UI state
    # ---------------------------------------------------------

    ui_state = UIStateMapper.map_state(state)

    # ---------------------------------------------------------
    # Completion page
    # ---------------------------------------------------------

    if ui_state == UIState.COMPLETION:

        return UIResponse(
            state=state,
            question_counter="",
            feedback="",
            written_text="",
            coding_text="",
            database_text="",
            written_visible=False,
            coding_visible=False,
            database_visible=False,
            ui_state=UIState.COMPLETION,
            final_feedback=f"### Final Feedback\n\n{feedback}",
            show_submit=False,
            show_retry=False,
            show_next=False,
        )

    # ---------------------------------------------------------
    # Current question
    # ---------------------------------------------------------

    question = session_dto.current_question

    if question is None:
        raise RuntimeError("UI attempted to render question but none exists")

    question_type = question.question_type

    is_last_question = state.is_last_question

    # ---------------------------------------------------------
    # Attempts counter
    # ---------------------------------------------------------

    attempts = state.attempts_by_question.get(question.question_id, 0)
    can_retry = attempts < MAX_ATTEMPTS

    # ---------------------------------------------------------
    # Interview progress panel
    # ---------------------------------------------------------

    counter = (
        f"### Interview Progress\n\n"
        f"Question {question.index} / {question.total}\n\n"
        f"Area: {question.area}\n\n"
        f"Attempts: {attempts} / {MAX_ATTEMPTS}"
    )

    # ---------------------------------------------------------
    # Build evaluation panel markdown
    # ---------------------------------------------------------

    evaluation_sections = []

    if score is not None:
        evaluation_sections.append(f"**Score:** {score} / 100")

    if feedback:
        evaluation_sections.append(f"**Feedback:**\n\n{feedback}")

    if test_results_lines:

        passed = sum(1 for t in test_results_lines if "✔" in t)
        total = len(test_results_lines)

        tests_block = "\n".join(test_results_lines)

        evaluation_sections.append(
            f"**Execution Results**\n\n"
            f"Tests passed: {passed} / {total}\n\n"
            f"{tests_block}"
        )

    if execution_status:
        evaluation_sections.append(f"**Execution status:** {execution_status}")

    if execution_error:
        evaluation_sections.append(f"⚠ **Execution error:** {execution_error}")

    # ---------------------------------------------------------
    # Max attempts warning
    # ---------------------------------------------------------

    if not can_retry:
        evaluation_sections.append(
            "⚠ **Maximum attempts reached. Please proceed to the next question.**"
        )

    # ---------------------------------------------------------
    # Build feedback markdown
    # ---------------------------------------------------------

    feedback_markdown = ""

    if evaluation_sections:
        feedback_markdown = "### Evaluation\n\n" + "\n\n".join(evaluation_sections)

    # ---------------------------------------------------------
    # UI mode
    # ---------------------------------------------------------

    is_feedback = ui_state == UIState.FEEDBACK

    return UIResponse(
        state=state,
        question_counter=counter,
        feedback=feedback_markdown,
        written_text=question.text,
        coding_text=question.text,
        database_text=question.text,
        written_visible=question_type == "written",
        coding_visible=question_type == "coding",
        database_visible=question_type == "database",
        ui_state=ui_state,
        show_submit=not is_feedback,
        show_submit_interactive=not is_feedback,
        show_retry=is_feedback and can_retry,
        show_next=is_feedback,
        next_label="Generate Report" if is_last_question else "Next Question",
    )


# =========================================================
# RETRY ANSWER
# =========================================================

def retry_answer(state: InterviewState):

    new_state = state.model_copy(deep=True)

    question = new_state.current_question

    if question:

        qid = question.id

        # increment attempts
        current = new_state.attempts_by_question.get(qid, 0)
        new_state.attempts_by_question[qid] = current + 1

        # reset question state
        new_state.reset_current_question()

    response = build_ui_response_from_state(new_state)

    # force QUESTION mode
    response.ui_state = UIState.QUESTION

    return response


# =========================================================
# NEXT QUESTION
# =========================================================


def next_question(state: InterviewState):

    from app.ui.ui_response import UIResponse
    from app.ui.ui_state import UIState
    from app.runtime.interview_runtime import get_runtime_evaluation_service

    # ---------------------------------------------------------
    # LAST QUESTION → GENERATE REPORT DIRECTLY
    # ---------------------------------------------------------

    if state.is_last_question:

        evaluation_service = get_runtime_evaluation_service()

        if state.final_evaluation is None:

            final_eval = evaluation_service.evaluate(
                per_question_evaluations=state.evaluations,
                questions=state.questions,
                interview_type=state.interview_type,
                role=state.role.type,
            )

            state.final_evaluation = final_eval

        # directly generate report
        response = build_ui_response_from_state(state)
        response.ui_state = UIState.REPORT

        return response

    # ---------------------------------------------------------
    # NORMAL FLOW
    # ---------------------------------------------------------

    state.advance_question()

    graph = get_runtime_graph()
    state = graph.invoke(state)

    return build_ui_response_from_state(state)


# =========================================================
# NEW INTERVIEW
# =========================================================

def new_interview():

    from app.ui.ui_response import UIResponse
    from app.ui.ui_state import UIState

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
# EXPORT PDF
# =========================================================

def export_pdf(state: InterviewState) -> str:

    evaluation_service = get_runtime_evaluation_service()

    if state.final_evaluation is None:

        final_eval = evaluation_service.evaluate(
            per_question_evaluations=state.evaluations,
            questions=state.questions,
            interview_type=state.interview_type,
            role=state.role.type,
        )

        state.final_evaluation = final_eval

    report = FinalReportDTO.from_state(state)

    os.makedirs("/mnt/data", exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    file_path = f"/mnt/data/{state.interview_id}_{timestamp}.pdf"

    export_service.export_pdf(report, file_path)

    return file_path


# =========================================================
# EXPORT JSON
# =========================================================

def export_json(state: InterviewState) -> str:

    evaluation_service = get_runtime_evaluation_service()

    if state.final_evaluation is None:

        final_eval = evaluation_service.evaluate(
            per_question_evaluations=state.evaluations,
            questions=state.questions,
            interview_type=state.interview_type,
            role=state.role.type,
        )

        state.final_evaluation = final_eval

    report = FinalReportDTO.from_state(state)

    os.makedirs("/mnt/data", exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    file_path = f"/mnt/data/{state.interview_id}_{timestamp}.json"

    export_service.export_json(report, file_path)

    return file_path
