# app/ui/state_handlers/navigation.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.shared.action_type import ActionType

from app.runtime.interview_runtime import run_interview_graph
from app.ui.mappers.loader_mapper import map_loader_progress
from app.ui.state_handlers.ui_builder import (
    build_ui_response_from_state,
)
from app.ui.constants.loader_steps import LoaderStep
from app.ui.adapters.ui_output_adapter import UIOutputAdapter
from app.core.logger import get_logger

logger = get_logger(__name__)


# =========================================================
# RETRY
# =========================================================
def retry_answer(state: InterviewState):

    if state is None or state.current_question is None:
        return UIOutputAdapter.to_gradio(build_ui_response_from_state(state))

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

    yield UIOutputAdapter.to_gradio(build_ui_response_from_state(new_state))


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
        new_state.current_step = LoaderStep.LOADING_NEXT_QUESTION

    new_state.current_progress = map_loader_progress(new_state.current_step)

    yield UIOutputAdapter.to_gradio(build_ui_response_from_state(new_state))

    # ---------------------------------------------------------
    # GRAPH
    # ---------------------------------------------------------
    try:
        new_state = run_interview_graph(new_state)
    except Exception as exc:
        logger.error("Interview graph failed during next/report: %s", exc)
        new_state.is_processing = False
        new_state.awaiting_user_input = True
        new_state.intent = ActionType.NONE
        new_state.current_step = None
        new_state.current_progress = 0
        yield UIOutputAdapter.to_gradio(build_ui_response_from_state(new_state))
        return

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

    yield UIOutputAdapter.to_gradio(build_ui_response_from_state(new_state))


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

    return UIOutputAdapter.to_gradio(response)
