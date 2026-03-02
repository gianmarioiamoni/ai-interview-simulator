# app/ui/state_handlers.py

from typing import Tuple, Any
import gradio as gr

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.role import Role, RoleType

from app.ui.sample_data_loader import load_sample_questions
from app.ui.views.report_view import build_report_markdown


# ---------------------------------------------------------
# Start Interview
# ---------------------------------------------------------


def start_interview(controller) -> Tuple:

    questions = load_sample_questions()

    state = InterviewState(
        interview_id="demo-session",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="Demo Company",
        language="en",
        questions=questions,
        progress=InterviewProgress.SETUP,
    )

    session_dto = controller.start_interview(state)

    return (
        state,
        session_dto.current_question.text,
        f"Question {session_dto.current_question.index}/{session_dto.current_question.total}",
        "",
        gr.update(visible=True),
        gr.update(visible=False),
    )


# ---------------------------------------------------------
# Submit Answer
# ---------------------------------------------------------


def submit_answer(
    controller,
    state: InterviewState,
    user_answer: str,
) -> Tuple:

    result, feedback = controller.submit_answer(state, user_answer)

    # ---------------------------------------------------------
    # Final report case
    # ---------------------------------------------------------

    if hasattr(result, "overall_score"):

        report = result

        report_text = build_report_markdown(report, state)

        return (
            state,
            "",
            "",
            "",
            gr.update(visible=False),
            gr.update(
                value=report_text,
                visible=True,
            ),
        )

    # ---------------------------------------------------------
    # In-progress case
    # ---------------------------------------------------------

    session = result

    return (
        state,
        session.current_question.text,
        f"Question {session.current_question.index}/{session.current_question.total}",
        "",
        gr.update(visible=True),
        gr.update(value=f"### Feedback\n\n{feedback}", visible=True),
    )
