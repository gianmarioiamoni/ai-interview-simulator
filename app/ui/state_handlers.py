# app/ui/state_handlers.py

from typing import Tuple, Any
import gradio as gr

from domain.contracts.interview_state import InterviewState
from domain.contracts.role import RoleType

from app.ui.sample_data_loader import load_sample_questions
from app.ui.views.report_view import build_report_markdown


# ---------------------------------------------------------
# Start Interview
# ---------------------------------------------------------

def start_interview(
    controller,
    role_name: str,
    company: str,
    language: str,
) -> Tuple[Any, ...]:

    role_type = RoleType[role_name]

    questions = load_sample_questions()

    state = InterviewState.create_initial(
        role_type=role_type,
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
        gr.update(visible=False),  # hide setup section
        gr.update(visible=True),  # show interview section
    )


# ---------------------------------------------------------
# Submit Answer
# ---------------------------------------------------------


def submit_answer(
    controller,
    state: InterviewState,
    user_answer: str,
) -> Tuple[Any, ...]:

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
            gr.update(visible=False),  # hide interview section
            gr.update(visible=True),  # show report section
            report_text,
        )

    # ---------------------------------------------------------
    # In-progress case
    # ---------------------------------------------------------

    session = result

    return (
        state,
        session.current_question.text,
        f"Question {session.current_question.index}/{session.current_question.total}",
        "",  # clear answer box
        gr.update(visible=True),  # keep interview visible
        gr.update(visible=False),  # keep report hidden
        gr.update(value=f"### Feedback\n\n{feedback}", visible=True),
    )
