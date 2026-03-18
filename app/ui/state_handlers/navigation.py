# app/ui/state_handlers/navigation.py

from domain.contracts.interview_state import InterviewState
from app.ui.ui_state import UIState

from app.runtime.interview_runtime import get_runtime_graph
from app.ui.state_handlers.ui_builder import build_ui_response_from_state
from app.ui.state_handlers.helpers import ensure_final_evaluation

MAX_ATTEMPTS = 3


def retry_answer(state: InterviewState):

    new_state = state.model_copy(deep=True)

    q = new_state.current_question

    if q:
        new_state.attempts_by_question[q.id] = (
            new_state.attempts_by_question.get(q.id, 0) + 1
        )
        new_state.reset_current_question()

    response = build_ui_response_from_state(new_state)
    response.ui_state = UIState.QUESTION

    return response


def next_question(state: InterviewState):

    if state.is_last_question:

        state = ensure_final_evaluation(state)

        response = build_ui_response_from_state(state)
        response.ui_state = UIState.REPORT

        return response.to_gradio_outputs()

    state.advance_question()

    graph = get_runtime_graph()
    state = graph.invoke(state)

    return build_ui_response_from_state(state).to_gradio_outputs()


def new_interview():

    from app.ui.ui_response import UIResponse

    return UIResponse(
        state=None,
        question_counter="",
        feedback="",
        written_text="",
        coding_text="",
        database_text="",
        written_visible=False,
        coding_visible=False,
        database_visible=False,
        ui_state=UIState.SETUP,
        final_feedback="",
        show_submit=False,
        show_retry=False,
        show_next=False,
    )
