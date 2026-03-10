# app/graph/nodes/progression_node.py

from domain.contracts.interview_state import InterviewState


def build_progression_node():

    def progression_node(state: InterviewState) -> InterviewState:

        question = state.current_question

        if question is None:
            return state

        next_index = state.current_question_index + 1

        return state.model_copy(update={"current_question_index": next_index})

    return progression_node
