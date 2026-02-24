# app/graph/nodes/ask_question_node.py

# AskQuestionNode
#
# Responsibility:
# Set current question pointer
# Do not touch followup_count

from domain.contracts.interview_state import InterviewState


def ask_question_node(state: InterviewState) -> InterviewState:
    # If interview has no questions
    if not state.questions:
        return state

    # Guard if already finished
    if state.current_question_index >= len(state.questions):
        return state

    # If we already have a current_question_id set and no answer for it,
    # we're waiting for the user response - don't change anything
    if state.current_question_id:
        has_answer = any(
            a.question_id == state.current_question_id for a in state.answers
        )
        state.awaiting_user_input = True
        if not has_answer:
            return state

    # Set the current question based on index
    question = state.questions[state.current_question_index]
    state.current_question_id = question.id

    return state
