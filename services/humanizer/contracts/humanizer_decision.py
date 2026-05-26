# services/humanizer/contracts/humanizer_decision.py

from enum import Enum


class HumanizerDecision(str, Enum):

    PLAIN_QUESTION = "plain_question"
    FOLLOW_UP = "follow_up"
    REMARK_AND_QUESTION = "remark_and_question"
    DIRECT_QUESTION = "direct_question"
    REMARK_PLUS_QUESTION = "remark_plus_question"
    NONE = "none"
