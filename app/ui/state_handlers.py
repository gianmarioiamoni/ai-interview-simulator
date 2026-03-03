# app/ui/state_handlers.py

import os
import gradio as gr

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
) -> tuple:

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

    return (
        state,
        session_dto.current_question.text,
        f"Question {session_dto.current_question.index}/{session_dto.current_question.total}",
        "",
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
    )


# =========================================================
# SUBMIT ANSWER
# =========================================================

def submit_answer(controller, state, user_answer):

    session_dto, feedback, completed = controller.submit_answer(state, user_answer)

    if completed:
        return (
            state,
            "",
            "",
            "",
            f"### Feedback\n\n{feedback}",
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(interactive=False),
        )

    return (
        state,
        session_dto.current_question.text,
        f"Question {session_dto.current_question.index}/{session_dto.current_question.total}",
        "",
        f"### Feedback\n\n{feedback}",
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(interactive=True),
    )


# =========================================================
# VIEW REPORT
# =========================================================

def view_report(
    controller: InterviewController,
    state: InterviewState,
):
    print("VIEW REPORT CALLED")
    print("STATE:", state)
    # Step 1 → Show loading immediately
    yield (
        gr.update(visible=False),  # interview
        gr.update(visible=False),  # completion
        gr.update(visible=True),   # report section
        "⏳ Generating final report... please wait.",
    )

    # Step 2 → Generate report
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

def export_pdf(controller: InterviewController, state: InterviewState):

    print("EXPORT PDF CALLED")

    report = controller.generate_final_report(state)

    os.makedirs("/mnt/data", exist_ok=True)
    file_path = "/mnt/data/interview_report.pdf"

    export_service.export_pdf(report, file_path)

    return file_path


# =========================================================
# EXPORT JSON
# =========================================================

def export_json(controller: InterviewController, state: InterviewState):

    print("EXPORT JSON CALLED")

    report = controller.generate_final_report(state)

    os.makedirs("/mnt/data", exist_ok=True)
    file_path = "/mnt/data/interview_report.json"

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
