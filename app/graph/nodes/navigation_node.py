# app/graph/nodes/navigation_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.shared.action_type import ActionType


def navigation_node(state: InterviewState) -> InterviewState:

    action = state.intent
    questions = state.questions or []
    current_index = state.current_question_index or 0

    if not questions:
        return state

    last_index = len(questions) - 1

    # ---------------------------------------------------------
    # RETRY
    # ---------------------------------------------------------
    if action == ActionType.RETRY:

        q = state.current_question
        new_state = state

        if q:
            new_state = new_state.clear_result_for_question(q.id)

        return new_state.model_copy(
            update={
                "awaiting_user_input": True,
                "last_feedback_bundle": None,
                "allowed_actions": [],
                "intent": None,  
            }
        )

    # ---------------------------------------------------------
    # NEXT
    # ---------------------------------------------------------
    if action == ActionType.NEXT:

        if current_index < last_index:
            return state.model_copy(
                update={
                    "current_question_index": current_index + 1,
                    "awaiting_user_input": True,
                    "last_feedback_bundle": None,
                    "allowed_actions": [],
                    "intent": None,  
                }
            )

        # LAST QUESTION → stay here
        return state.model_copy(
            update={
                "awaiting_user_input": True,
                "intent": None,  
            }
        )

    # ---------------------------------------------------------
    # GENERATE REPORT
    # ---------------------------------------------------------
    if action == ActionType.GENERATE_REPORT:

        return state.model_copy(
            update={
                "awaiting_user_input": False,
                "intent": None,  
            }
        )

    return state
