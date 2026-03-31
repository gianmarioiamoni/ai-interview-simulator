# app/graph/nodes/navigation_node.py


def navigation_node(state: InterviewState) -> InterviewState:

    action = state.last_action
    questions = state.questions or []
    current_index = state.current_question_index or 0

    if not questions:
        return state

    last_index = len(questions) - 1

    # ---------------------------------------------------------
    # RETRY
    # ---------------------------------------------------------

    if action == ActionType.RETRY:
        return state.model_copy(
            update={
                "awaiting_user_input": True,
                "last_action": None,  # 🔥 consume
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
                    "last_action": None,  # 🔥 consume
                }
            )

        return state.model_copy(
            update={
                "awaiting_user_input": True,
                "last_action": None,  
            }
        )

    return state
