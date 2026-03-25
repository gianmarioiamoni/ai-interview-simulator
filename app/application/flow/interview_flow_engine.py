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

        return state.with_current_question(state.questions[0], 0)

    # =========================================================
    # SUBMIT
    # =========================================================

    def submit(self, state: InterviewState, event) -> InterviewState:

        return self._graph.invoke(
            {
                "state": state,
                "event": event,
            }
        )

    # =========================================================
    # NEXT
    # =========================================================

    def next(self, state: InterviewState) -> InterviewState:

        if not state.current_question:
            return state

        # -----------------------------------------------------
        # END
        # -----------------------------------------------------

        if state.is_last_question:
            return state.model_copy(update={"progress": "completed"})

        # -----------------------------------------------------
        # ADAPTIVE SELECTION (NEW)
        # -----------------------------------------------------

        return self._select_next_question(state)

    # =========================================================
    # ADAPTIVE DIFFICULTY
    # =========================================================

    def _select_next_question(self, state: InterviewState) -> InterviewState:

        current_index = state.current_question_index
        next_index = current_index + 1

        if next_index >= len(state.questions):
            return state

        # -----------------------------------------------------
        # PERFORMANCE
        # -----------------------------------------------------

        performance = getattr(state, "performance_level", "medium")

        # -----------------------------------------------------
        # SIMPLE STRATEGY
        # -----------------------------------------------------
        # For now we DO NOT change question selection,
        # but we prepare the hook for future logic

        next_question = state.questions[next_index]

        # -----------------------------------------------------
        # FUTURE HOOK (IMPORTANT)
        # -----------------------------------------------------
        # Here you will:
        # - filter by difficulty
        # - reorder questions
        # - inject dynamic questions

        # Example (future):
        # if performance == "weak":
        #     next_question = self._find_question_by_difficulty(state, "easy")

        # -----------------------------------------------------
        # IMMUTABLE UPDATE
        # -----------------------------------------------------

        return state.with_current_question(next_question, next_index)
