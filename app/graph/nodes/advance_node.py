# app/graph/nodes/advance_node.py

from domain.contracts.interview_state import InterviewState


def advance_node(state: InterviewState) -> InterviewState:

    if not state.questions:
        return state

    if not state.is_last_question:
        state.advance_question()

    return state
