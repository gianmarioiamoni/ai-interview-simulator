# app/graph/nodes/navigation_node.py

from domain.contracts.interview_state import InterviewState
from domain.policies.navigation_policy import NavigationPolicy


def navigation_node(state: InterviewState) -> InterviewState:
    # Defensive: node must always produce valid state

    action = state.get("last_action")
    questions = state.get("questions", [])
    current_index = state.get("current_question_index", 0)

    # Safety fallback
    if not questions:
        return state

    # Retry → no navigation
    if action == "retry":
        return {
            **state,
            "awaiting_user_input": True,
        }

    # Next → compute next index
    if action == "next":
        next_index = NavigationPolicy.select_next_question_index(
            questions=questions,
            current_index=current_index,
        )

        return {
            **state,
            "current_question_index": next_index,
            "current_question": questions[next_index],
            "awaiting_user_input": True,
        }

    # Default safety (important for node isolation)
    return {
        **state,
        "awaiting_user_input": True,
    }
