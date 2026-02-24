# app/graph/nodes/ask_question_node.py

# AskQuestionNode
#
# Responsibility:
# Set current_question
# Reset execution_result
# Do not touch followup_count

from domain.contracts.interview_state import InterviewState


def ask_question_node(state: InterviewState) -> InterviewState:
    # Guard if already finished
    if state.current_question_index >= len(state.questions):
        return state

    question = state.questions[state.current_question_index]

    state.current_question = question
    state.execution_result = None
    state.evaluation_result = None
    state.current_answer = None

    return state
