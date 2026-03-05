# app/ui/ui_state.py

from enum import Enum


class UIState(str, Enum):

    SETUP = "setup"
    QUESTION = "question"
    COMPLETION = "completion"
    REPORT = "report"
