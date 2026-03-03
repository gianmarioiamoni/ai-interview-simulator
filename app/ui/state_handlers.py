# app/ui/state_handlers.py

import gradio as gr

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_type import InterviewType
from domain.contracts.role import RoleType

from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.views.report_view import build_report_markdown
from app.ui.sample_data_loader import load_sample_questions
from app.ui.controllers.interview_controller import InterviewController


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

    role_type = RoleType[role_name]
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
        "",  # clear feedback
        gr.update(visible=False),  # hide setup
        gr.update(visible=True),  # show interview
        gr.update(visible=False),  # hide completion
        gr.update(visible=False),  # hide report
    )


# =========================================================
# SUBMIT ANSWER
# =========================================================


def submit_answer(
    controller: InterviewController,
    state: InterviewState,
    user_answer: str,
) -> tuple:

    session_dto, feedback, completed = controller.submit_answer(state, user_answer)

    # ---------------------------------------------------------
    # Interview completed
    # ---------------------------------------------------------

    if completed:

        return (
            state,
            "",  # no new question
            "",  # no counter
            "",  # clear answer box
            f"### Feedback\n\n{feedback}",
            gr.update(visible=True),  # interview still visible
            gr.update(visible=True),  # completion section visible
            gr.update(interactive=False),  # disable submit button
        )

    # ---------------------------------------------------------
    # Still in progress
    # ---------------------------------------------------------

    if isinstance(session_dto, InterviewSessionDTO):

        return (
            state,
            session_dto.current_question.text,
            f"Question {session_dto.current_question.index}/{session_dto.current_question.total}",
            "",  # clear answer
            f"### Feedback\n\n{feedback}",
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(interactive=True),
        )

    raise TypeError("Unexpected state in submit_answer")


# =========================================================
# VIEW REPORT
# =========================================================


def view_report(
    controller: InterviewController,
    state: InterviewState,
) -> tuple:

    # Now heavy work happens HERE
    report = controller.generate_final_report(state)

    report_text = build_report_markdown(report)

    return (
        gr.update(visible=False),  # hide interview
        gr.update(visible=False),  # hide completion
        gr.update(visible=True),  # show report
        report_text,
    )


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
