# app/graph/nodes/termination_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress


def termination_node(state: InterviewState) -> InterviewState:
    if not state.questions:
        state.progress = InterviewProgress.COMPLETED
        return state

    if state.current_question_index >= len(state.questions):
        state.progress = InterviewProgress.COMPLETED
        return state

    state.progress = InterviewProgress.IN_PROGRESS
    return state
