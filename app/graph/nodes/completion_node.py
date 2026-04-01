# app/graph/nodes/completion_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.action_type import ActionType


def completion_node(state: InterviewState) -> InterviewState:

    questions = state.questions or []
    current_index = state.current_question_index or 0

    if not questions:
        return state

    last_index = len(questions) - 1

    # COMPLETION ONLY AFTER NEXT ON LAST QUESTION
    if (
        current_index == last_index
        and state.last_action is None 
        and not state.awaiting_user_input  
        and state.last_feedback_bundle is not None
    ):
        return state.model_copy(update={"is_completed": True})

    return state
