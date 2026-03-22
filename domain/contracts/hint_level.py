# domain/contracts/hint_level.py

from enum import Enum


class HintLevel(str, Enum):
    BASIC = "basic"
    TARGETED = "targeted"
    SOLUTION = "solution"
