# app/application/flow/interview_flow_engine.py

from domain.contracts.interview_state import InterviewState
from app.runtime.interview_runtime import get_runtime_graph
from domain.contracts.question import QuestionDifficulty


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
        # ADAPTIVE SELECTION
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

        if performance == "weak":
            target_difficulty = QuestionDifficulty.EASY
        elif performance == "medium":
            target_difficulty = QuestionDifficulty.MEDIUM
        else:
            target_difficulty = QuestionDifficulty.HARD

        # -----------------------------------------------------
        # ADAPTIVE SELECTION
        # -----------------------------------------------------

        next_question, resolved_index = self._find_question_by_difficulty(
            state,
            target_difficulty,
            next_index,
        )

        # -----------------------------------------------------
        # IMMUTABLE UPDATE (IMPORTANT FIX)
        # -----------------------------------------------------

        return state.with_current_question(next_question, resolved_index)

    # =========================================================
    # FIND QUESTION BY DIFFICULTY (FINAL VERSION)
    # =========================================================

    def _find_question_by_difficulty(
        self,
        state: InterviewState,
        target_difficulty: QuestionDifficulty,
        start_index: int,
    ):

        asked_ids = set(getattr(state, "asked_question_ids", []))

        # -----------------------------------------------------
        # 1. TRY MATCH DIFFICULTY (NO REPEAT)
        # -----------------------------------------------------

        for i in range(start_index, len(state.questions)):
            q = state.questions[i]

            if q.id in asked_ids:
                continue

            if getattr(q, "difficulty", None) == target_difficulty:
                return q, i

        # -----------------------------------------------------
        # 2. FALLBACK → ANY NON-ASKED QUESTION
        # -----------------------------------------------------

        for i in range(start_index, len(state.questions)):
            q = state.questions[i]

            if q.id not in asked_ids:
                return q, i

        # -----------------------------------------------------
        # 3. FINAL FALLBACK → SEQUENTIAL (ALLOW REPEAT)
        # -----------------------------------------------------

        return state.questions[start_index], start_index
