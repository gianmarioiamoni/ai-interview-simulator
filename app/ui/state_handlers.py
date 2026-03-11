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

from app.graph.interview_graph import build_interview_graph

from app.ai.test_generation.ai_test_generator import AITestGenerator

from services.report_export_service import ReportExportService
from services.interview_evaluation_service import InterviewEvaluationService

from infrastructure.llm.llm_factory import get_llm
from app.ui.mappers.interview_state_mapper import InterviewStateMapper


export_service = ReportExportService()
test_generator = AITestGenerator()
mapper = InterviewStateMapper()


# =========================================================
# START INTERVIEW
# =========================================================


def start_interview(
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

    graph = build_interview_graph(get_llm())

    state = graph.invoke(state)

    return build_ui_response_from_state(state)


# =========================================================
# GENERIC ANSWER SUBMIT
# =========================================================


def submit_written_answer(
    state: InterviewState,
    user_answer: str,
):

    return _submit_answer(state, user_answer)


def submit_coding_answer(
    state: InterviewState,
    user_answer: str,
):

    return _submit_answer(state, user_answer)


def submit_database_answer(
    state: InterviewState,
    user_answer: str,
):

    return _submit_answer(state, user_answer)


# =========================================================
# INTERNAL ANSWER HANDLER
# =========================================================


def _submit_answer(state: InterviewState, user_answer: str):

    question = state.current_question

    if question is None:
        raise RuntimeError("No current question available")

    answer = Answer(
        question_id=question.id,
        content=user_answer,
        attempt=1,
    )

    state.answers.append(answer)

    graph = build_interview_graph(get_llm())

    state = graph.invoke(state)

    return build_ui_response_from_state(state)


# =========================================================
# UI RESPONSE BUILDER (PUBLIC)
# =========================================================


def build_ui_response_from_state(state: InterviewState) -> UIResponse:

    session_dto = mapper.to_session_dto(state)

    feedback = ""

    if state.evaluations:
        feedback = state.evaluations[-1].feedback

    execution_error = None

    if state.execution_results:
        last_execution = state.execution_results[-1]
        if not last_execution.success:
            execution_error = last_execution.error

    completed = state.progress.name == "COMPLETED"

    if completed:

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

    question = session_dto.current_question
    question_type = question.question_type

    counter = f"Question {question.index}/{question.total}"

    feedback_text = feedback

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
    state: InterviewState,
) -> str:

    evaluation_service = InterviewEvaluationService(get_llm())

    if state.final_evaluation is None:

        final_eval = evaluation_service.evaluate(
            per_question_evaluations=state.evaluations,
            questions=state.questions,
            interview_type=state.interview_type,
            role=state.role.type,
        )

        state.final_evaluation = final_eval

    report = mapper.to_final_report_dto(state)

    os.makedirs("/mnt/data", exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    file_path = f"/mnt/data/{state.interview_id}_{timestamp}.pdf"

    export_service.export_pdf(report, file_path)

    return file_path


# =========================================================
# EXPORT JSON
# =========================================================


def export_json(
    state: InterviewState,
) -> str:

    evaluation_service = InterviewEvaluationService(get_llm())

    if state.final_evaluation is None:

        final_eval = evaluation_service.evaluate(
            per_question_evaluations=state.evaluations,
            questions=state.questions,
            interview_type=state.interview_type,
            role=state.role.type,
        )

        state.final_evaluation = final_eval

    report = mapper.to_final_report_dto(state)

    os.makedirs("/mnt/data", exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    file_path = f"/mnt/data/{state.interview_id}_{timestamp}.json"

    export_service.export_json(report, file_path)

    return file_path
