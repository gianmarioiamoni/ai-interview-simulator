# app/ui/state_handlers.py

from typing import Tuple, Any
import gradio as gr

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_type import InterviewType
from domain.contracts.role import RoleType
from app.ui.dto.interview_session_dto import InterviewSessionDTO

from app.ui.sample_data_loader import load_sample_questions
from app.ui.controllers.interview_controller import InterviewController
from app.ui.dto.final_report_dto import FinalReportDTO


# =========================================================
# START INTERVIEW
# =========================================================


def start_interview(
    controller,
    role_name: str,
    interview_type_name: str,
    company: str,
    language: str,
) -> Tuple[Any, ...]:

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
        "",  # feedback reset
        gr.update(visible=False),  # hide setup
        gr.update(visible=True),   # show interview
        gr.update(visible=False),  # completion hidden
        gr.update(visible=False),  # report hidden
    )


# =========================================================
# SUBMIT ANSWER
# =========================================================


def submit_answer(
    controller : InterviewController,
    state: InterviewState,
    user_answer: str,
) -> Tuple[Any, ...]:

    result, feedback = controller.submit_answer(state, user_answer)

   # ------------------------------------------------------------
   # Final report case
   # ------------------------------------------------------------

    if isinstance(result, FinalReportDTO):

        return (
            state,
            "",  # no new question
            "",  # no counter
            "",  # clear answer
            f"### Feedback\n\n{feedback}",
            gr.update(visible=True),  # interview section is still visible
            gr.update(visible=True),  # completion section is visible
            gr.update(interactive=False),  # submit button is disabled
            result,
        )

    # ------------------------------------------------------------
    # In-progress interview case
    # ------------------------------------------------------------

    if isinstance(result, InterviewSessionDTO):
        session_dto = result

        return (
            state,
            session_dto.current_question.text,
            f"Question {session_dto.current_question.index}/{session_dto.current_question.total}",
            "",  # clear answer
            f"### Feedback\n\n{feedback}",
            gr.update(visible=True),  # interview section is still visible
            gr.update(visible=False),  # completion section is hidden
            gr.update(interactive=True),  # submit button is enabled
            None,  # no report
        )

    # ------------------------------------------------------------
    # Unknown result case
    # ------------------------------------------------------------

    raise TypeError(f"Unknown result type: {type(result)}")

# =========================================================
# RESET INTERVIEW
# =========================================================


def reset_interview():

    return (
        None,  # reset state
        gr.update(visible=True),  # show setup
        gr.update(visible=False),  # hide interview
        gr.update(visible=False),  # hide completion
        gr.update(visible=False),  # hide report
    )
