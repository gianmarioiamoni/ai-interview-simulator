# domain/contracts/quality.py

from enum import Enum


class Quality(str, Enum):
    INCORRECT = "incorrect"
    PARTIAL = "partial"
    CORRECT = "correct"
    OPTIMAL = "optimal"
    INEFFICIENT = "inefficient"
