# app/ui/state_handlers/navigation.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.shared.action_type import ActionType

from app.runtime.interview_runtime import run_interview_graph
from app.ui.state_handlers.ui_builder import build_ui_response_from_state


# =========================================================
# RETRY
# =========================================================


def retry_answer(state: InterviewState):

    if state is None or state.current_question is None:
        return build_ui_response_from_state(state).to_gradio_outputs()

    new_state = state.model_copy(deep=True)

    new_state.last_action = ActionType.RETRY

    new_state = run_interview_graph(new_state)

    return build_ui_response_from_state(new_state).to_gradio_outputs()


# =========================================================
# NEXT
# =========================================================


def next_question(state: InterviewState):

    new_state = state.model_copy(deep=True)

    # ---------------------------------------------------------
    # STEP 1 — ACTION
    # ---------------------------------------------------------
    if ActionType.GENERATE_REPORT in state.allowed_actions:
        new_state.last_action = ActionType.GENERATE_REPORT
    else:
        new_state.last_action = ActionType.NEXT

    # ---------------------------------------------------------
    # STEP 2 — LOCK UI
    # ---------------------------------------------------------
    new_state.awaiting_user_input = False

    yield build_ui_response_from_state(new_state).to_gradio_outputs()

    # ---------------------------------------------------------
    # STEP 3 — RUN GRAPH
    # ---------------------------------------------------------
    new_state = run_interview_graph(new_state)

    # ---------------------------------------------------------
    # STEP 4 — UNLOCK UI
    # ---------------------------------------------------------
    new_state.awaiting_user_input = True

    yield build_ui_response_from_state(new_state).to_gradio_outputs()


# =========================================================
# NEW INTERVIEW
# =========================================================


def new_interview(state: InterviewState):

    new_state = InterviewState.create_empty()
    response = build_ui_response_from_state(new_state)

    response.role_visible = True
    response.interview_type_visible = True
    response.company_visible = True
    response.language_visible = True

    response.state = new_state

    return response.to_gradio_outputs()
