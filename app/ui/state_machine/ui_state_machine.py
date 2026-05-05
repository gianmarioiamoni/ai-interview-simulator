# app/ui/state_machine/ui_state_machine.py

from app.ui.ui_state import UIState
from domain.contracts.interview_state import InterviewState


class UIStateMachine:

    @staticmethod
    def resolve(state: InterviewState | None) -> UIState:

        print("\n=== UI STATE RESOLVE ===")

        if state is None:
            print("state is None → SETUP\n")
            return UIState.SETUP

        print("has_question:", bool(state.current_question))
        print("is_completed:", getattr(state, "is_completed", None))
        print("has_feedback:", bool(state.last_feedback_bundle))
        print("awaiting_input:", getattr(state, "awaiting_user_input", None))
        print("allowed_actions:", state.allowed_actions)

        # -----------------------------------------------------
        # REPORT
        # -----------------------------------------------------
        if state.interview_evaluation is not None:
            print("→ resolved UI state: REPORT\n")
            return UIState.REPORT

        # -----------------------------------------------------
        # COMPLETION
        # -----------------------------------------------------
        if state.is_completed:
            print("→ resolved UI state: COMPLETION\n")
            return UIState.COMPLETION

        # -----------------------------------------------------
        # SETUP
        # -----------------------------------------------------
        if not state.current_question:
            print("→ resolved UI state: SETUP\n")
            return UIState.SETUP

        # -----------------------------------------------------
        # FEEDBACK
        # -----------------------------------------------------
        if state.last_feedback_bundle is not None and state.allowed_actions:
            print("→ resolved UI state: FEEDBACK\n")
            return UIState.FEEDBACK

        # -----------------------------------------------------
        # PROCESSING (FIX)
        # -----------------------------------------------------
        # PROCESSING deve essere esplicito, non dedotto da awaiting_user_input
        if getattr(state, "is_processing", False):
            print("→ resolved UI state: PROCESSING\n")
            return UIState.PROCESSING

        # -----------------------------------------------------
        # DEFAULT = QUESTION
        # -----------------------------------------------------
        print("→ resolved UI state: QUESTION\n")
        return UIState.QUESTION
