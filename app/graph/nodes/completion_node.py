# app/graph/nodes/completion_node.py

from domain.contracts.interview_state import InterviewState


def completion_node(state: InterviewState) -> InterviewState:

    questions = state.questions or []
    current_index = state.current_question_index or 0

    if not questions:
        return state

    # completed when index goes beyond last question
    if current_index >= len(questions):
        return state.model_copy(update={"is_completed": True})

    return state
