# app/ui/state_handlers/navigation.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.action_type import ActionType

from app.ui.ui_state import UIState
from app.ui.ui_response import UIResponse
from app.ui.state_handlers.ui_builder import build_ui_response_from_state

from app.runtime.interview_runtime import run_interview_graph


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

    new_state.last_action = ActionType.NONE
    new_state.awaiting_user_input = True
    new_state.last_feedback_bundle = None

    response = build_ui_response_from_state(new_state)
    response.ui_state = UIState.QUESTION

    return response


# =========================================================
# NEXT / GENERATE REPORT
# =========================================================


def next_question(state: InterviewState):

    new_state = state.model_copy(deep=True)

    # -----------------------------------------------------
    # 🔥 CRITICAL FIX: distinguish NEXT vs GENERATE_REPORT
    # -----------------------------------------------------

    if ActionType.GENERATE_REPORT in state.allowed_actions:
        new_state.last_action = ActionType.GENERATE_REPORT
    else:
        new_state.last_action = ActionType.NEXT

    # -----------------------------------------------------
    # RUN GRAPH
    # -----------------------------------------------------

    new_state = run_interview_graph(new_state)

    # -----------------------------------------------------
    # REPORT FLOW
    # -----------------------------------------------------

    if new_state.is_completed:

        response = build_ui_response_from_state(new_state)
        response.ui_state = UIState.REPORT

        return response.to_gradio_outputs()

    # -----------------------------------------------------
    # NORMAL FLOW
    # -----------------------------------------------------

    return build_ui_response_from_state(new_state).to_gradio_outputs()


# =========================================================
# NEW INTERVIEW
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
