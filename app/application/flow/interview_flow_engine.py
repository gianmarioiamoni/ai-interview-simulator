# app/application/flow/interview_flow_engine.py

from domain.contracts.interview_state import InterviewState
from app.runtime.interview_runtime import get_runtime_graph


class InterviewFlowEngine:

    def __init__(self):
        self._graph = get_runtime_graph()

    # =========================================================
    # START
    # =========================================================

    def start(self, state: InterviewState) -> InterviewState:
        # initialize first question only

        if state.questions:
            state.current_question = state.questions[0]

        return state

    # =========================================================
    # SUBMIT ANSWER
    # =========================================================

    def submit_answer(self, state: InterviewState) -> InterviewState:
        # run full graph (evaluation + feedback)

        return self._graph.invoke(state)

    # =========================================================
    # NEXT QUESTION
    # =========================================================

    def next_question(self, state: InterviewState) -> InterviewState:

        if not state.current_question:
            return state

        current_index = next(
            (
                i
                for i, q in enumerate(state.questions)
                if q.id == state.current_question.id
            ),
            None,
        )

        if current_index is None:
            return state

        next_index = current_index + 1

        if next_index >= len(state.questions):
            state.is_completed = True
            return state

        state.current_question = state.questions[next_index]

        return state
