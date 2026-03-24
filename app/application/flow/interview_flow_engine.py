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

        if not state.questions:
            return state

        # IMMUTABLE UPDATE
        return state.with_current_question(state.questions[0], 0)

    # =========================================================
    # SUBMIT
    # =========================================================

    def submit(self, state: InterviewState, event) -> InterviewState:

        # the graph should know how to handle the event
        return self._graph.invoke({
            "state": state,
            "event": event,
        })

    # =========================================================
    # NEXT
    # =========================================================

    def next(self, state: InterviewState) -> InterviewState:

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

        # -----------------------------------------------------
        # END
        # -----------------------------------------------------

        if next_index >= len(state.questions):
            return state.model_copy(update={"is_completed": True})

        # -----------------------------------------------------
        # NEXT QUESTION
        # -----------------------------------------------------

        return state.model_copy(
            update={
                "current_question": state.questions[next_index],
                "current_question_index": next_index,
            }
        )
