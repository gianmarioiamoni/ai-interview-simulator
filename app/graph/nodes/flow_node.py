# app/graph/nodes/flow_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress


def flow_node(state: InterviewState) -> InterviewState:

    state.awaiting_user_input = False

    if not state.questions:
        state.progress = InterviewProgress.COMPLETED
        return state

    next_index = state.current_question_index + 1

    if next_index >= len(state.questions):

        state.progress = InterviewProgress.COMPLETED
        return state

    state.current_question_index = next_index

    state.progress = InterviewProgress.IN_PROGRESS

    return state
