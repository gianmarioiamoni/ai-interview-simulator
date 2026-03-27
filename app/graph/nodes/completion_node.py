# app/graph/nodes/completion_node.py

from domain.contracts.interview_state import InterviewState


def completion_node(state: InterviewState) -> InterviewState:

    questions = state.get("questions", [])
    current_index = state.get("current_question_index", 0)

    if not questions:
        return state

    is_last = current_index >= len(questions) - 1

    if is_last and state.get("last_action") == "next":
        return {
            **state,
            "is_completed": True,
        }

    return state
