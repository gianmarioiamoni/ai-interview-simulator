# app/graph/nodes/advance_node.py

from domain.contracts.interview_state import InterviewState


def advance_node(state: InterviewState) -> InterviewState:

    q = state.current_question

    if q is None:
        return state

    # Do not advance if the question is not processed yet
    if not state.is_question_processed(q):
        return state

    if not state.is_last_question:
        state.advance_question()

    return state
