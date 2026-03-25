# domain/contracts/hint_level.py

from enum import Enum


class HintLevel(str, Enum):
    NONE = "none"
    BASIC = "basic"
    TARGETED = "targeted"
    SOLUTION = "solution"
