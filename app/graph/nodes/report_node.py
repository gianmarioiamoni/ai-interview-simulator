# app/graph/nodes/report_node.py

from domain.contracts.interview_state import InterviewState

from app.ui.state_handlers.helpers import ensure_final_evaluation


def report_node(state: InterviewState) -> InterviewState:

    state = ensure_final_evaluation(state)

    return state
