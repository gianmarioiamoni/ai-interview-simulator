# app/ui/state_handlers.py

import os
from datetime import datetime

import gradio as gr

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_type import InterviewType
from domain.contracts.role import RoleType

from app.ui.controllers.interview_controller import InterviewController
from app.ui.sample_data_loader import load_sample_questions
from app.ui.ui_state import UIState
from app.ui.ui_response import UIResponse

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
# SUBMIT ANSWER
# =========================================================

def submit_answer(
    controller: InterviewController,
    state,
    user_answer: str,
):

    session_dto, feedback, completed = controller.submit_answer(
        state,
        user_answer,
    )

    # ---------------------------------------------------------
    # Interview completed
    # ---------------------------------------------------------

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
        )

    # ---------------------------------------------------------
    # Next question
    # ---------------------------------------------------------

    question = session_dto.current_question

    question_text = question.text
    question_type = question.question_type
    counter = f"Question {question.index}/{question.total}"

    written_visible = question_type == "written"
    coding_visible = question_type == "coding"
    database_visible = question_type == "database"

    return UIResponse(
        state=state,
        question_counter=counter,
        feedback=f"### Feedback\n\n{feedback}",
        written_text=question_text,
        coding_text=question_text,
        database_text=question_text,
        written_visible=written_visible,
        coding_visible=coding_visible,
        database_visible=database_visible,
        ui_state=UIState.QUESTION,
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
