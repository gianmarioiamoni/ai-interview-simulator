# app/ui/state_machine/ui_state_machine.py

from app.ui.ui_state import UIState
from domain.contracts.interview_state import InterviewState


class UIStateMachine:

    @staticmethod
    def resolve(state: InterviewState | None) -> UIState:

        if state is None:
            return UIState.SETUP

        # -----------------------------------------------------
        # REPORT
        # -----------------------------------------------------

        if state.interview_evaluation is not None:
            return UIState.REPORT

        # -----------------------------------------------------
        # COMPLETION
        # -----------------------------------------------------

        if state.is_completed:
            return UIState.COMPLETION

        current_q = state.current_question

        if not current_q:
            return UIState.SETUP

        # FEEDBACK ONLY IF:
        # - the graph has explicitly decided
        # - there is a real feedback
        # - there are available actions

        if (
            state.awaiting_user_input
            and state.allowed_actions
            and state.last_feedback_bundle is not None
        ):
            return UIState.FEEDBACK

        # -----------------------------------------------------
        # DEFAULT → QUESTION
        # -----------------------------------------------------

        return UIState.QUESTION
