# app/graph/nodes/termination_node.py


# Responsibility:
# - Check if interview is finished

from domain.contracts.interview_state import InterviewState
def termination_node(state: InterviewState) -> InterviewState:
    if state.current_question_index >= len(state.questions):
        state.finished = True
        return state

    state.finished = False
    return state
