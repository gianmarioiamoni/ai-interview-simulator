# services/humanizer/contracts/humanizer_decision.py

from enum import Enum


class HumanizerDecision(str, Enum):

    PLAIN_QUESTION = "plain_question"
    FOLLOW_UP = "follow_up"
    DIRECT_QUESTION = "direct_question"
    REMARK_PLUS_QUESTION = "remark_plus_question"
    NONE = "none"
