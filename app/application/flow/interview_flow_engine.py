# app/application/flow/interview_flow_engine.py

from domain.contracts.interview_state import InterviewState
from app.runtime.interview_runtime import get_runtime_graph
from domain.contracts.question import QuestionDifficulty


class InterviewFlowEngine:

    def __init__(self, llm=None):
        self._graph = get_runtime_graph(llm=llm)

    # =========================================================
    # START
    # =========================================================

    def start(self, state: InterviewState) -> InterviewState:

        if not state.questions:
            return state

        return state.with_current_question(state.questions[0], 0)

    # =========================================================
    # SUBMIT
    # =========================================================

    def submit(self, state: InterviewState, event=None) -> InterviewState:

        # graph = evaluation pipeline
        return self._graph.invoke(state)

    # =========================================================
    # NEXT
    # =========================================================

    def next(self, state: InterviewState) -> InterviewState:

        if not state.current_question:
            return state

        # -----------------------------------------------------
        # NEW: decision-driven flow (STEP 2.6)
        # -----------------------------------------------------

        if getattr(state, "last_action", None) == "retry":
            return state

        # -----------------------------------------------------
        # END
        # -----------------------------------------------------

        if state.is_last_question:
            return state.model_copy(update={"progress": "completed"})

        # -----------------------------------------------------
        # ADVANCE QUESTION
        # -----------------------------------------------------

        new_state = self._select_next_question(state)

        # -----------------------------------------------------
        # RUN GRAPH
        # -----------------------------------------------------

        return self._graph.invoke(new_state)
