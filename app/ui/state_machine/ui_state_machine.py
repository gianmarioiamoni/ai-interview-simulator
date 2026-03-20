# app/ui/state_machine/ui_state_machine.py

from app.ui.ui_state import UIState
from domain.contracts.interview_state import InterviewState


class UIStateMachine:

    @staticmethod
    def resolve(state: InterviewState | None) -> UIState:
        # =========================================================
        # SETUP
        # =========================================================

        if state is None:
            return UIState.SETUP

        # =========================================================
        # REPORT (final evaluation available)
        # =========================================================

        if state.final_evaluation is not None:
            return UIState.REPORT

        # =========================================================
        # COMPLETION (optional)
        # =========================================================

        if state.is_completed:
            return UIState.COMPLETION

        # =========================================================
        # FEEDBACK (question already processed)
        # =========================================================

        current_q = state.current_question

        if current_q and state.is_question_processed(current_q):
            return UIState.FEEDBACK

        # =========================================================
        # QUESTION (default)
        # =========================================================

        return UIState.QUESTION
