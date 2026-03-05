# app/core/flow/interview_flow_state.py

from enum import Enum


class InterviewFlowState(str, Enum):

    SETUP = "setup"
    QUESTION = "question"
    FOLLOW_UP = "follow_up"
    EXECUTION = "execution"
    COMPLETION = "completion"
    REPORT = "report"
