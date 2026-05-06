# app/ui/state_machine/ui_state_machine.py

from app.ui.ui_state import UIState
from domain.contracts.interview_state import InterviewState


class UIStateMachine:

    @staticmethod
    def resolve(state: InterviewState | None) -> UIState:


        if state is None:
            return UIState.SETUP

        # REPORT
        if state.interview_evaluation is not None:
            print("→ resolved UI state: REPORT\n")
            return UIState.REPORT

        # COMPLETION
        if state.is_completed:
            print("→ resolved UI state: COMPLETION\n")
            return UIState.COMPLETION

        # SETUP
        if not state.current_question:
            print("→ resolved UI state: SETUP\n")
            return UIState.SETUP

        # FEEDBACK
        if (
            state.awaiting_user_input
            and state.allowed_actions
            and state.last_feedback_bundle is not None
        ):
            print("→ resolved UI state: FEEDBACK\n")
            return UIState.FEEDBACK

        # DEFAULT = QUESTION
        print("→ resolved UI state: QUESTION\n")
        return UIState.QUESTION
