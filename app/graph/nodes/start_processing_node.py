# app/graph/nodes/start_processing_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.shared.action_type import ActionType

from app.ui.constants.loader_steps import LoaderStep


def start_processing_node(state: InterviewState) -> InterviewState:

    if state.intent == ActionType.GENERATE_REPORT:
        step = LoaderStep.PREPARING_REPORT
    else:
        step = LoaderStep.SUBMITTING

    return state.model_copy(
        update={
            "is_processing": True,
            "current_step": step,
        }
    )
