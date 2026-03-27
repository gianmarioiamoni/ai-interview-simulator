# app/ui/state_handlers/navigation.py

from domain.contracts.interview_state import InterviewState

from app.ui.ui_state import UIState
from app.ui.ui_response import UIResponse
from app.ui.state_handlers.ui_builder import build_ui_response_from_state
from app.ui.state_handlers.helpers import ensure_final_evaluation

from app.graph.interview_graph import graph

MAX_ATTEMPTS = 3


# =========================================================
# RETRY 
# =========================================================

def retry_answer(state: InterviewState):

    if state is None or state.current_question is None:
        return UIResponse(
            state=None,
            ui_state=UIState.SETUP,
            show_submit=False,
            show_retry=False,
            show_next=False,
        )

    new_state = state.model_copy(deep=True)

    q = new_state.current_question

    if q:
        new_state = new_state.clear_result_for_question(q.id)

    response = build_ui_response_from_state(new_state)
    response.ui_state = UIState.QUESTION

    return response


# =========================================================
# NEXT 
# =========================================================

def next_question(state: InterviewState):

    state.last_action = "next"

    state = graph.invoke(state)

    if state.is_completed:

        state = ensure_final_evaluation(state)

        response = build_ui_response_from_state(state)
        response.ui_state = UIState.REPORT

        return response.to_gradio_outputs()

    return build_ui_response_from_state(state).to_gradio_outputs()


# =========================================================
# NEW INTERVIEW (FIXED)
# =========================================================


def new_interview():

    return UIResponse(
        state=None,
        question_counter="",
        feedback_markdown="",  
        feedback_quality=None,
        written_display="",
        coding_display="",
        database_display="",
        written_visible=False,
        coding_visible=False,
        database_visible=False,
        written_editor_visible=False,
        coding_editor_visible=False,
        database_editor_visible=False,
        ui_state=UIState.SETUP,
        final_feedback="",
        report_output="",
        show_submit=False,
        show_submit_interactive=False,
        show_retry=False,
        show_next=False,
    )
