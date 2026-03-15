# app/ui/mappers/ui_state_mapper.py

from app.ui.ui_state import UIState
from domain.contracts.interview_state import InterviewState


class UIStateMapper:
    # Maps InterviewState (domain) to UIState (presentation).
    # Keeps UI decision logic isolated from UI handlers.

    @staticmethod
    def map_state(state: InterviewState) -> UIState:

        if state.is_completed:
            return UIState.COMPLETION

        question = state.current_question

        if question is None:
            return UIState.SETUP

        if state.last_answer:

            if (
                state.last_answer.question_id == question.id
                and state.is_question_processed(question)
            ):
                return UIState.FEEDBACK

        return UIState.QUESTION
