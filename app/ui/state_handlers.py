# app/ui/state_handlers.py

import os
from datetime import datetime

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_type import InterviewType
from domain.contracts.role import RoleType

from app.ui.controllers.interview_controller import InterviewController
from app.ui.sample_data_loader import load_sample_questions
from app.ui.views.report_view import build_report_markdown

from services.report_export_service import ReportExportService


export_service = ReportExportService()


# =========================================================
# START INTERVIEW
# =========================================================


def start_interview(
    controller: InterviewController,
    role_name: str,
    interview_type_name: str,
    company: str,
    language: str,
):

    role_type = RoleType[role_name.replace(" ", "_")]
    interview_type = InterviewType[interview_type_name]

    questions = load_sample_questions(interview_type)

    state = InterviewState.create_initial(
        role_type=role_type,
        interview_type=interview_type,
        company=company,
        language=language,
        questions=questions,
        interview_id="session-1",
    )

    session_dto = controller.start_interview(state)

    question = session_dto.current_question

    question_text = question.text
    question_type = question.question_type
    counter = f"Question {question.index}/{question.total}"

    return (
        state,
        question_text,
        counter,
        question_type,
    )


# =========================================================
# SUBMIT ANSWER
# =========================================================


def submit_answer(
    controller: InterviewController,
    state: InterviewState,
    user_answer: str,
):

    session_dto, feedback, completed = controller.submit_answer(
        state,
        user_answer,
    )

    if completed:

        return (
            state,
            None,
            "",
            f"### Final Question Feedback\n\n{feedback}",
            False,
            True,
        )

    question_dto = session_dto.current_question

    return (
        state,
        question_dto,
        f"### Feedback\n\n{feedback}",
        "",
        True,
        False,
    )


# =========================================================
# EXPORT PDF
# =========================================================


def export_pdf(
    controller: InterviewController,
    state: InterviewState,
) -> str:

    report = controller.generate_final_report(state)

    os.makedirs("/mnt/data", exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    file_path = f"/mnt/data/{state.interview_id}_{timestamp}.pdf"

    export_service.export_pdf(report, file_path)

    return file_path


# =========================================================
# EXPORT JSON
# =========================================================


def export_json(
    controller: InterviewController,
    state: InterviewState,
) -> str:

    report = controller.generate_final_report(state)

    os.makedirs("/mnt/data", exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    file_path = f"/mnt/data/{state.interview_id}_{timestamp}.json"

    export_service.export_json(report, file_path)

    return file_path


# =========================================================
# RESET
# =========================================================


def reset_interview():

    return (
        None,
        True,
        False,
        False,
        False,
    )
