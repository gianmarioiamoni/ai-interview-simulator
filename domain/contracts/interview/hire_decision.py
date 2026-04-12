# domain/contracts/hire_decision.py

from enum import Enum


class HireDecision(str, Enum):
    NO_HIRE = "no_hire"
    LEAN_NO_HIRE = "lean_no_hire"
    LEAN_HIRE = "lean_hire"
    HIRE = "hire"
