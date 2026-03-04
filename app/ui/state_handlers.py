# app/ui/state_handlers.py

import os
import gradio as gr
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
    question_type = question.question_type

    written_visible = question_type == "written"
    coding_visible = question_type == "coding"
    database_visible = question_type == "database"

    return (
        state,
        f"Question {question.index}/{question.total}",
        "",  # feedback_output
        question.text,
        question.text,
        question.text,
        gr.update(visible=written_visible),
        gr.update(visible=coding_visible),
        gr.update(visible=database_visible),
        gr.update(visible=False),  # setup_section
        gr.update(visible=True),  # interview_section
        gr.update(visible=False),  # completion_section
        gr.update(visible=False),  # report_section
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
            "",  # question_counter
            f"### Feedback\n\n{feedback}",
            "",
            "",
            "",
            gr.update(visible=False),  # written_container
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),  # interview_section
            gr.update(visible=True),  # completion_section
        )

    question = session_dto.current_question
    question_type = question.question_type

    written_visible = question_type == "written"
    coding_visible = question_type == "coding"
    database_visible = question_type == "database"

    return (
        state,
        f"Question {question.index}/{question.total}",
        f"### Feedback\n\n{feedback}",
        question.text,
        question.text,
        question.text,
        gr.update(visible=written_visible),
        gr.update(visible=coding_visible),
        gr.update(visible=database_visible),
        gr.update(visible=True),  # interview_section
        gr.update(visible=False),  # completion_section
    )


# =========================================================
# VIEW REPORT
# =========================================================


def view_report(
    controller: InterviewController,
    state: InterviewState,
):

    yield (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
        "⏳ Generating final report... please wait.",
    )

    report = controller.generate_final_report(state)
    report_text = build_report_markdown(report)

    yield (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
        report_text,
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
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )
