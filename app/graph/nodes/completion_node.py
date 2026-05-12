# app/graph/nodes/completion_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.shared.action_type import ActionType

from app.ui.constants.loader_steps import LoaderStep


def completion_node(state: InterviewState) -> InterviewState:

    if state.last_action == ActionType.GENERATE_REPORT:

        working_state = state.model_copy(
            update={
                "current_step": LoaderStep.GENERATING_REPORT,
                "is_completed": True,
                "awaiting_user_input": False,
                "last_action": ActionType.NONE,
            }
        )

        return working_state

    return state
