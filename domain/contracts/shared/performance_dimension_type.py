# domain/contracts/shared/performance_dimension_type.py

from enum import Enum


class PerformanceDimensionType(str, Enum):
    TECHNICAL_DEPTH = "technical_depth"
    PROBLEM_SOLVING = "problem_solving"
    COMMUNICATION = "communication"
    SYSTEM_DESIGN = "system_design"
