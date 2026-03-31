# app/graph/nodes/navigation_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.action_type import ActionType


def navigation_node(state: InterviewState) -> InterviewState:

    action = state.last_action
    questions = state.questions or []
    current_index = state.current_question_index or 0

    if not questions:
        return state

    # ---------------------------------------------------------
    # RETRY
    # ---------------------------------------------------------

    if action == ActionType.RETRY:
        return state.model_copy(
            update={
                "awaiting_user_input": True,
                # ❗ KEEP last_action
            }
        )

    # ---------------------------------------------------------
    # NEXT
    # ---------------------------------------------------------

    if action == "next":

        last_index = len(questions) - 1

        if current_index < last_index:
            return state.model_copy(
                update={
                    "current_question_index": current_index + 1,
                    # ❗ KEEP last_action
                }
            )

        return state.model_copy(
            update={
                "current_question_index": last_index,
                # ❗ KEEP last_action
            }
        )

    return state
