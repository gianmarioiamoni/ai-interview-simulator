# app/graph/nodes/completion_node.py

from domain.contracts.interview_state import InterviewState


def completion_node(state: InterviewState) -> InterviewState:

    print(f"[DEBUG] completion_node - is_completed: {state.is_completed}")

    questions = state.questions or []
    current_index = state.current_question_index or 0

    if not questions:
        return state

    last_index = len(questions) - 1

    if current_index >= last_index and state.current_question is not None:
        return state.model_copy(
            update={
                "is_completed": True,
                "last_action": None,  # consume here
            }
        )

    return state
