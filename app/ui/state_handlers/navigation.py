# app/ui/state_handlers/navigation.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.shared.action_type import ActionType

from app.runtime.interview_runtime import run_interview_graph
from app.ui.state_handlers.ui_builder import build_ui_response_from_state

from app.ui.constants.loader_steps import LoaderStep


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
# NEXT / GENERATE REPORT
# =========================================================
def next_question(state: InterviewState):

    new_state = state.model_copy(deep=True)

    is_report = ActionType.GENERATE_REPORT in state.allowed_actions

    # ---------------------------------------------------------
    # STEP 1 — SET ACTION
    # ---------------------------------------------------------
    new_state.last_action = ActionType.GENERATE_REPORT if is_report else ActionType.NEXT

    # ---------------------------------------------------------
    # STEP 2 — LOCK UI + INITIAL LOADER
    # ---------------------------------------------------------
    new_state.awaiting_user_input = False

    yield build_ui_response_from_state(new_state).to_gradio_outputs()

    # ---------------------------------------------------------
    # STEP 3 — REPORT PIPELINE (STREAMING)
    # ---------------------------------------------------------
    if is_report:

        yield build_ui_response_from_state(new_state).to_gradio_outputs()

        yield build_ui_response_from_state(new_state).to_gradio_outputs()

        new_state = run_interview_graph(new_state)

        yield build_ui_response_from_state(new_state).to_gradio_outputs()

    else:
        # NORMAL NEXT
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

    # RESET UI COMPLETO
    response.role_visible = True
    response.interview_type_visible = True
    response.company_visible = True
    response.language_visible = True

    response.state = new_state

    return response.to_gradio_outputs()
