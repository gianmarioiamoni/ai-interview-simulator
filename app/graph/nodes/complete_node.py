# app/graph/nodes/complete_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress


def complete_node(state: InterviewState) -> InterviewState:

    print("COMPLETE NODE")

    state.progress = InterviewProgress.COMPLETED

    return state
