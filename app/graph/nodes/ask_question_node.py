# app/graph/nodes/ask_question_node.py

from domain.contracts.interview_state import InterviewState


def ask_question_node(state: InterviewState) -> InterviewState:

    # No questions
    if not state.questions:
        return state

    # Interview finished
    if state.current_question_index >= len(state.questions):
        return state

    question = state.current_question

    if question is None:
        return state

    # Check if we already have an answer for the current question
    has_answer = any(a.question_id == question.id for a in state.answers)

    # If no answer yet → wait for user input
    if not has_answer:
        state.awaiting_user_input = True
        return state

    # If answer already exists → allow pipeline to continue
    state.awaiting_user_input = False

    return state
