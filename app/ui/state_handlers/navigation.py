# app/ui/state_handlers/navigation.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.shared.action_type import ActionType

from app.runtime.interview_runtime import run_interview_graph
from app.ui.mappers.loader_mapper import map_loader_progress
from app.ui.state_handlers.ui_builder import (
    build_ui_response_from_state,
)
from app.ui.constants.loader_steps import LoaderStep


# =========================================================
# RETRY
# =========================================================
def retry_answer(state: InterviewState):

    if state is None or state.current_question is None:
        return build_ui_response_from_state(state).to_gradio_outputs()

    new_state = state.model_copy(deep=True)

    # ---------------------------------------------------------
    # INTENT
    # ---------------------------------------------------------
    new_state.intent = ActionType.RETRY

    # ---------------------------------------------------------
    # LOCK UI
    # ---------------------------------------------------------
    new_state.is_processing = True
    new_state.awaiting_user_input = False


    # ---------------------------------------------------------
    # GRAPH
    # ---------------------------------------------------------
    new_state = run_interview_graph(new_state)

    # ---------------------------------------------------------
    # UNLOCK UI
    # ---------------------------------------------------------
    new_state.is_processing = False
    new_state.awaiting_user_input = True
    new_state.intent = ActionType.NONE

    yield build_ui_response_from_state(new_state).to_gradio_outputs()


# =========================================================
# NEXT / GENERATE REPORT
# =========================================================
def next_question(state: InterviewState):

    new_state = state.model_copy(deep=True)

    is_report = ActionType.GENERATE_REPORT in state.allowed_actions

    # ---------------------------------------------------------
    # INTENT
    # ---------------------------------------------------------
    new_state.intent = ActionType.GENERATE_REPORT if is_report else ActionType.NEXT

    # ---------------------------------------------------------
    # LOCK UI
    # ---------------------------------------------------------
    new_state.is_processing = True
    new_state.awaiting_user_input = False

    if is_report:
        new_state.current_step = LoaderStep.PREPARING_REPORT
    else:
        new_state.current_step = LoaderStep.SUBMITTING

    new_state.current_progress = map_loader_progress(new_state.current_step)

    yield build_ui_response_from_state(new_state).to_gradio_outputs()

    # ---------------------------------------------------------
    # GRAPH
    # ---------------------------------------------------------
    new_state = run_interview_graph(new_state)

    # ---------------------------------------------------------
    # RESET LOADER STATE
    # ---------------------------------------------------------
    new_state.current_step = None
    new_state.current_progress = 0
    
    # ---------------------------------------------------------
    # UNLOCK UI
    # ---------------------------------------------------------
    new_state.is_processing = False
    new_state.intent = ActionType.NONE

    # IMPORTANT:
    # report flow MUST stay non-interactive
    if not is_report:
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
