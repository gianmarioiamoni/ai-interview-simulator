# app/ui/state_handlers.py

import os
from datetime import datetime

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_type import InterviewType
from domain.contracts.role import RoleType
from domain.contracts.question import QuestionType
from domain.contracts.answer import Answer

from app.ui.sample_data_loader import load_sample_questions
from app.ui.ui_state import UIState
from app.ui.ui_response import UIResponse

from app.core.flow.interview_flow_engine import InterviewFlowEngine
from app.core.flow.interview_flow_state import InterviewFlowState

from app.ai.test_generation.ai_test_generator import AITestGenerator

from services.report_export_service import ReportExportService


export_service = ReportExportService()
test_generator = AITestGenerator()


# =========================================================
# START INTERVIEW
# =========================================================


def start_interview(
    flow_engine: InterviewFlowEngine,
    role_name: str,
    interview_type_name: str,
    company: str,
    language: str,
):

    role_type = RoleType[role_name.replace(" ", "_")]
    interview_type = InterviewType[interview_type_name]

    questions = load_sample_questions(interview_type)

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
        interview_type=interview_type,
        company=company,
        language=language,
        questions=questions,
        interview_id="session-1",
    )

    result = flow_engine.start(state)

    session_dto = result["session"]

    question = session_dto.current_question
    question_type = question.question_type

    return UIResponse(
        state=state,
        question_counter=f"Question {question.index}/{question.total}",
        feedback="",
        written_text=question.text,
        coding_text=question.text,
        database_text=question.text,
        written_visible=question_type == "written",
        coding_visible=question_type == "coding",
        database_visible=question_type == "database",
        ui_state=UIState.QUESTION,
    )


# =========================================================
# GENERIC ANSWER SUBMIT 
# =========================================================

def submit_written_answer(
    flow_engine: InterviewFlowEngine,
    state: InterviewState,
    user_answer: str,
):

    result = flow_engine.process_answer(
        state,
        user_answer,
    )

    return _build_ui_response(
        state,
        result,
        result.get("execution_error"),
    )


def submit_coding_answer(
    flow_engine: InterviewFlowEngine,
    state: InterviewState,
    user_answer: str,
):

    result = flow_engine.process_answer(
        state,
        user_answer,
    )

    return _build_ui_response(
        state,
        result,
        result.get("execution_error"),
    )


def submit_database_answer(
    flow_engine: InterviewFlowEngine,
    state: InterviewState,
    user_answer: str,
):

    result = flow_engine.process_answer(
        state,
        user_answer,
    )

    return _build_ui_response(
        state,
        result,
        result.get("execution_error"),
    )


# =========================================================
# BUILD UI RESPONSE
# =========================================================

def _build_ui_response(state, result, execution_error=None):

    flow_state = result["flow_state"]

    if flow_state == InterviewFlowState.COMPLETION:

        feedback = result["feedback"]

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
            final_feedback=f"### Feedback\n\n{feedback}",
        )

    session_dto = result["session"]

    question = session_dto.current_question
    question_type = question.question_type

    counter = f"Question {question.index}/{question.total}"

    evaluation = next(
        (e for e in state.evaluations if e.question_id == question.question_id),
        None,
    )

    feedback_text = evaluation.feedback if evaluation else result["feedback"]

    if execution_error:
        feedback_text += f"\n\n⚠ Execution error: {execution_error}"

    return UIResponse(
        state=state,
        question_counter=counter,
        feedback=f"### Feedback\n\n{feedback_text}",
        written_text=question.text,
        coding_text=question.text,
        database_text=question.text,
        written_visible=question_type == "written",
        coding_visible=question_type == "coding",
        database_visible=question_type == "database",
        ui_state=UIState.QUESTION,
    )


# =========================================================
# EXPORT PDF
# =========================================================

def export_pdf(
    flow_engine: InterviewFlowEngine,
    state: InterviewState,
) -> str:

    report = flow_engine.generate_report(state)

    os.makedirs("/mnt/data", exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    file_path = f"/mnt/data/{state.interview_id}_{timestamp}.pdf"

    export_service.export_pdf(report, file_path)

    return file_path


# =========================================================
# EXPORT JSON
# =========================================================


def export_json(
    flow_engine: InterviewFlowEngine,
    state: InterviewState,
) -> str:

    report = flow_engine.generate_report(state)

    os.makedirs("/mnt/data", exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    file_path = f"/mnt/data/{state.interview_id}_{timestamp}.json"

    export_service.export_json(report, file_path)

    return file_path
