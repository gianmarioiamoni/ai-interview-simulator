# app/graph/nodes/completion_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.action_type import ActionType


def completion_node(state: InterviewState) -> InterviewState:

    print(f"[DEBUG] completion_node - is_completed: {state.is_completed}")

    questions = state.questions or []
    current_index = state.current_question_index or 0

    if not questions:
        return state

    last_index = len(questions) - 1

    # ---------------------------------------------------------
    # COMPLETE ONLY IF USER EXPLICITLY PRESSED NEXT ON LAST QUESTION
    # ---------------------------------------------------------

    if current_index == last_index and state.last_action == ActionType.NEXT:
        return state.model_copy(
            update={
                "is_completed": True,
                "last_action": ActionType.NONE,
            }
        )

    return state
