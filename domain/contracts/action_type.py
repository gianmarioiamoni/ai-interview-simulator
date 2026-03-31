# domain/contracts/action_type.py

from enum import Enum


class ActionType(str, Enum):
    RETRY = "retry"
    NEXT = "next"
    NONE = "none"