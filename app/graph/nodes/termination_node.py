# app/graph/nodes/termination_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress


def termination_node(state: InterviewState) -> InterviewState:
    
    state.total_score = state.computed_total_score

    if not state.questions:
        state.progress = InterviewProgress.COMPLETED
        state.awaiting_user_input = False
        return state

    # Check if we're waiting for an answer to the current question
    if state.current_question_id:
        has_answer = any(
            a.question_id == state.current_question_id for a in state.answers
        )
        if not has_answer:
            state.progress = InterviewProgress.IN_PROGRESS
            state.awaiting_user_input = True
            return state

    # Reset awaiting flag when we have an answer
    state.awaiting_user_input = False

    if state.current_question_index >= len(state.questions):
        state.progress = InterviewProgress.COMPLETED
        return state

    state.progress = InterviewProgress.IN_PROGRESS
    return state
