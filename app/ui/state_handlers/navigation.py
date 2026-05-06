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

    q = new_state.current_question

    if q:
        new_state = new_state.clear_result_for_question(q.id)

    new_state.last_action = ActionType.RETRY
    new_state.awaiting_user_input = True
    new_state.last_feedback_bundle = None

    return build_ui_response_from_state(new_state).to_gradio_outputs()


# =========================================================
# NEXT
# =========================================================


def next_question(state: InterviewState):

    new_state = state.model_copy(deep=True)

    if ActionType.GENERATE_REPORT in state.allowed_actions:
        new_state.last_action = ActionType.GENERATE_REPORT
    else:
        new_state.last_action = ActionType.NEXT

    new_state = run_interview_graph(new_state)

    return build_ui_response_from_state(new_state).to_gradio_outputs()


# =========================================================
# NEW INTERVIEW
# =========================================================


def new_interview(state: InterviewState):

    new_state = InterviewState.create_empty()

    return build_ui_response_from_state(new_state).to_gradio_outputs()
