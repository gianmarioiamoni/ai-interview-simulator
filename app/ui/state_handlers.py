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

    return (
        state,
        question.text,
        f"Question {question.index}/{question.total}",
        question.question_type,
        gr.update(visible=False),  # setup
        gr.update(visible=True),  # interview
    )


# =========================================================
# SUBMIT ANSWER
# =========================================================


def submit_answer(controller, state, user_answer):

    session_dto, feedback, completed = controller.submit_answer(
        state,
        user_answer,
    )

    if completed:

        return (
            state,
            "",
            "",
            "",
            f"### Feedback\n\n{feedback}",
            gr.update(visible=False),
            gr.update(visible=True),
        )

    question = session_dto.current_question

    return (
        state,
        question.text,
        f"Question {question.index}/{question.total}",
        question.question_type,
        f"### Feedback\n\n{feedback}",
        gr.update(visible=True),
        gr.update(visible=False),
    )
