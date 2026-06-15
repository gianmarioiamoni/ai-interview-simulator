# app/graph/nodes/report_node.py

from domain.contracts.interview_state import InterviewState


def report_node(state: InterviewState) -> InterviewState:

    return state.model_copy(
        update={
            "is_processing": False,
            "current_step": None,
        }
    )
