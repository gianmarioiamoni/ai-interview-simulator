# app/graph/nodes/navigation_node.py

from domain.contracts.interview_state import InterviewState


def navigation_node(state: InterviewState) -> InterviewState:

    action = state.last_action
    questions = state.questions or []
    current_index = state.current_question_index or 0

    if not questions:
        return state

    # ---------------------------------------------------------
    # RETRY
    # ---------------------------------------------------------

    if action == "retry":
        return state.model_copy(
            update={
                "awaiting_user_input": True,
                "last_action": None,
            }
        )

    # ---------------------------------------------------------
    # NEXT
    # ---------------------------------------------------------

    if action == "next":

        # last question → move beyond last (completion handled later)
        if current_index >= len(questions) - 1:
            return state.model_copy(
                update={
                    "current_question_index": current_index + 1,
                    "last_action": None,
                }
            )

        # normal next
        return state.model_copy(
            update={
                "current_question_index": current_index + 1,
                "last_action": None,
            }
        )

    # ---------------------------------------------------------
    # DEFAULT
    # ---------------------------------------------------------

    return state
