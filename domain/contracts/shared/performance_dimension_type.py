# domain/contracts/shared/performance_dimension_type.py

from enum import Enum


class PerformanceDimensionType(str, Enum):
    TECHNICAL_DEPTH = "technical_depth"
    PROBLEM_SOLVING = "problem_solving"
    COMMUNICATION = "communication"
    SYSTEM_DESIGN = "system_design"
    # Added in V1.1 M2 (ADR-040). Replaces TRADE_OFF_AWARENESS.
    # Covers trade-offs, prioritisation, failure-mode reasoning,
    # operational decisions, and engineering judgment calls.
    ENGINEERING_JUDGMENT = "engineering_judgment"
