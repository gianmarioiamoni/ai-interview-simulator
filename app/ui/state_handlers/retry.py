# domain/contracts/retry.py

from domain.contracts.interview_state import InterviewState
from app.ui.state_handlers.ui_builder import build_ui_response_from_state

from app.ui.ui_response import UIResponse
from app.ui.ui_state import UIState

from app.runtime.interview_runtime import run_interview_graph


def retry_answer(state: InterviewState):

    if state is None or state.current_question is None:
        return UIResponse(state=None, ui_state=UIState.SETUP, show_submit=False, show_retry=False, show_next=False)

    new_state = state.model_copy(deep=True)

    q = new_state.current_question

    if q:
        new_state = new_state.clear_result_for_question(q.id)

    new_state.last_action = "retry"

    # CORRECT GRAPH INVOCATION
    new_state = run_interview_graph(new_state)

    response = build_ui_response_from_state(new_state)
    response.ui_state = UIState.QUESTION

    return response
