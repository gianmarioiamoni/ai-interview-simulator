# app/graph/nodes/completion_node.py

from domain.contracts.interview_state import InterviewState
from app.ui.constants.loader_steps import LoaderStep


def completion_node(state: InterviewState) -> InterviewState:

    questions = state.questions or []
    current_index = state.current_question_index or 0

    if not questions:
        return state

    planned_total = (
        len(state.planned_areas)
        if state.adaptive_interview_enabled and state.planned_areas
        else len(questions)
    )

    last_index = max(planned_total - 1, 0)

    # -----------------------------------------------------
    # COMPLETE INTERVIEW
    # -----------------------------------------------------
    if (
        current_index >= last_index
        and len(questions) >= planned_total
        and not state.awaiting_user_input
    ):
        return state.model_copy(
            update={
                "is_completed": True,
            }
        )

    return state
