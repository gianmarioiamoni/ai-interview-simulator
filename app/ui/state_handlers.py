# app/ui/state_handlers.py

from typing import Tuple, Any
import gradio as gr

from domain.contracts.interview_state import InterviewState
from app.ui.views.report_view import build_report_markdown


# ---------------------------------------------------------
# Submit Answer
# ---------------------------------------------------------


def submit_answer(
    controller,
    state: InterviewState,
    user_answer: str,
) -> Tuple[Any, ...]:
    # Handles answer submission flow.
    #
    # Responsibilities:
    # - Delegates business logic to controller
    # - Distinguishes between in-progress and final report case
    # - Maps domain output to UI components
    #

    result, feedback = controller.submit_answer(state, user_answer)

    # ---------------------------------------------------------
    # Final report case
    # ---------------------------------------------------------

    if hasattr(result, "overall_score"):

        report = result
        report_text = build_report_markdown(report, state)

        return (
            state,  # state
            "",  # question_text
            "",  # question_counter
            "",  # answer_box (cleared)
            gr.update(visible=False),  # submit_button hidden
            gr.update(  # report_output shown
                value=report_text,
                visible=True,
            ),
        )

    # ---------------------------------------------------------
    # In-progress case
    # ---------------------------------------------------------

    session = result

    return (
        state,  # updated state already mutated inside controller
        session.current_question.text,
        f"Question {session.current_question.index}/{session.current_question.total}",
        "",  # clear answer box
        gr.update(visible=True),
        gr.update(
            value=f"### Feedback\n\n{feedback}",
            visible=True,
        ),
    )
