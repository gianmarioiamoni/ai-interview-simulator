# domain/contracts/reasoning/profile_dimension.py

from enum import Enum


class ProfileDimension(str, Enum):
    """Five scoreable dimensions assessed by the Interview Reasoner.

    Aligns with PerformanceDimensionType (existing four) plus
    ENGINEERING_JUDGMENT added in M2 (ADR-040).
    """
    TECHNICAL_DEPTH = "technical_depth"
    PROBLEM_SOLVING = "problem_solving"
    COMMUNICATION = "communication"
    SYSTEM_DESIGN = "system_design"
    # Replaces TRADE_OFF_AWARENESS (ADR-040).
    # Covers: trade-offs, prioritisation, failure-mode reasoning, operational decisions.
    ENGINEERING_JUDGMENT = "engineering_judgment"
