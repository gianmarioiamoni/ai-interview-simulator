# app/ui/state_machine/ui_state_machine.py

from app.ui.ui_state import UIState
from domain.contracts.interview_state import InterviewState


class UIStateMachine:

    @staticmethod
    def resolve(state: InterviewState | None) -> UIState:
        # Determine the UI state based on the domain state.

        # SETUP
        if state is None:
            return UIState.SETUP

        # REPORT
        if state.final_evaluation is not None:
            return UIState.REPORT

        # COMPLETION (optional, if you really use it)
        if state.is_completed:
            return UIState.COMPLETION

        # FEEDBACK
        if state.current_question and state.is_question_processed(
            state.current_question
        ):
            return UIState.FEEDBACK

        # QUESTION
        return UIState.QUESTION
