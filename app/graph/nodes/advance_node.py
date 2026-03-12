# app/graph/nodes/advance_node.py

from domain.contracts.interview_state import InterviewState


def advance_node(state: InterviewState) -> InterviewState:

    if not state.questions:
        return state

    if state.last_answer is None:
        return state

    if state.last_answer.question_id != state.current_question.id:
        return state

    if not state.is_question_processed(state.current_question):
        return state

    if not state.is_last_question:
        state.advance_question()

    return state
