# app/ui/state_handlers/navigation.py

from domain.contracts.interview_state import InterviewState

from app.ui.ui_state import UIState
from app.ui.ui_response import UIResponse
from app.ui.state_handlers.ui_builder import build_ui_response_from_state
from app.ui.state_handlers.helpers import ensure_final_evaluation

from app.runtime.interview_runtime import get_runtime_graph

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

    return UIResponse(
        state=None,
        question_counter="",
        feedback="",
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
