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
            return UIState.REPORT

        # COMPLETION (optional, redundant)
        # you can also remove it
        if state.is_completed:
            return UIState.COMPLETION

        current_q = state.current_question

        if current_q and state.is_question_processed(current_q):
            return UIState.FEEDBACK

        return UIState.QUESTION
