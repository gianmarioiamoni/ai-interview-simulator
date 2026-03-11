# app/graph/nodes/advance_node.py

from domain.contracts.interview_state import InterviewState


def advance_node(state: InterviewState) -> InterviewState:

    if state.is_last_question:
        return state

    state.advance_question()

    return state
