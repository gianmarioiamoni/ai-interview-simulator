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

from app.runtime.interview_runtime import (
    get_runtime_graph,
    get_runtime_evaluation_service,
)

export_service = ReportExportService()
test_generator = AITestGenerator()


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

def submit_answer(
    state: InterviewState,
    user_answer: str,
):

    question = state.current_question

    if question is None:
        raise RuntimeError("No current question available")

    event = AnswerSubmittedEvent(
        question_id=question.id,
        content=user_answer,
    )

    state = state.apply_event(event)

    graph = get_runtime_graph()
    state = graph.invoke(state)

    return build_ui_response_from_state(state)


# =========================================================
# UI RESPONSE BUILDER
# =========================================================


def build_ui_response_from_state(state: InterviewState) -> UIResponse:

    session_dto = InterviewSessionDTO.from_state(state)

    feedback = ""
    execution_error = None

    # ---------------------------------------------------------
    # Retrieve result for last answered question
    # ---------------------------------------------------------

    if state.last_answer:

        question_id = state.last_answer.question_id

        result = state.get_result_for_question(question_id)

        if result:

            if result.evaluation:
                feedback = result.evaluation.feedback

            if result.execution and not result.execution.success:
                execution_error = result.execution.error

    # ---------------------------------------------------------
    # Interview completed
    # ---------------------------------------------------------

    if state.is_completed:

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
        )

    # ---------------------------------------------------------
    # Current question
    # ---------------------------------------------------------

    question = session_dto.current_question
    question_type = question.question_type

    counter = f"Question {question.index}/{question.total}"

    feedback_text = feedback

    if execution_error:
        feedback_text += f"\n\n⚠ Execution error: {execution_error}"

    # ---------------------------------------------------------
    # Detect FEEDBACK state
    # ---------------------------------------------------------

    ui_state = UIState.QUESTION

    if state.last_answer and question:

        if (
            state.last_answer.question_id == question.id
            and state.is_question_processed(question)
        ):
            ui_state = UIState.FEEDBACK

    return UIResponse(
        state=state,
        question_counter=counter,
        feedback=f"### Feedback\n\n{feedback_text}" if feedback_text else "",
        written_text=question.text,
        coding_text=question.text,
        database_text=question.text,
        written_visible=question_type == "written",
        coding_visible=question_type == "coding",
        database_visible=question_type == "database",
        ui_state=ui_state,
    )


# =========================================================
# RETRY ANSWER
# =========================================================

def retry_answer(state: InterviewState):

    # Simply return the same question without advancing
    # UI will switch back to QUESTION mode

    response = build_ui_response_from_state(state)

    response.ui_state = UIState.QUESTION

    return response


# =========================================================
# NEXT QUESTION
# =========================================================

def next_question(state: InterviewState):

    graph = get_runtime_graph()

    state = graph.invoke(state)

    return build_ui_response_from_state(state)


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
