# app/ui/ui_state.py

from enum import Enum


class UIState(str, Enum):

    SETUP = "setup"
    QUESTION = "question"
    FEEDBACK = "feedback"
    RETRY = "retry"
    COMPLETION = "completion"
    REPORT = "report"

    def is_interview_state(self) -> bool:
        return self in {UIState.QUESTION, UIState.FEEDBACK}
