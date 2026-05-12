# app/graph/nodes/completion_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.shared.action_type import ActionType

from app.ui.constants.loader_steps import LoaderStep


def completion_node(state: InterviewState) -> InterviewState:

    if state.last_action == ActionType.GENERATE_REPORT:

        working_state = state.model_copy(
            update={
                "current_step": LoaderStep.GENERATING_REPORT,
                "awaiting_user_input": False,
            }
        )

        working_state = working_state.model_copy(
            update={
                "is_completed": True,
            }
        )

        return working_state.model_copy(
            update={
                "current_step": None,
                "awaiting_user_input": True,
                "last_action": ActionType.NONE,
            }
        )

    return state
