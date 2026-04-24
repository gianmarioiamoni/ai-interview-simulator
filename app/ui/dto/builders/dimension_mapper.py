# app/ui/dto/builders/dimension_mapper.py

from domain.contracts.feedback.error_type import ErrorType
from domain.contracts.shared.performance_dimension_type import (
    PerformanceDimensionType,
)


class DimensionMapper:

    @staticmethod
    def map(error_type: ErrorType, execution=None):

        # =====================================================
        # LOGIC ERRORS → PROBLEM SOLVING
        # =====================================================

        if error_type == ErrorType.LOGIC:
            return PerformanceDimensionType.PROBLEM_SOLVING

        # =====================================================
        # RUNTIME / SYNTAX / SIGNATURE → TECHNICAL DEPTH
        # =====================================================

        if error_type in (
            ErrorType.RUNTIME,
            ErrorType.SYNTAX,
            ErrorType.SIGNATURE,
        ):
            return PerformanceDimensionType.TECHNICAL_DEPTH

        # =====================================================
        # TIMEOUT → SYSTEM DESIGN (performance / complexity)
        # =====================================================

        if error_type == ErrorType.TIMEOUT:
            return PerformanceDimensionType.SYSTEM_DESIGN

        # =====================================================
        # PERFORMANCE HEURISTIC (execution-based)
        # =====================================================

        if execution:

            exec_time = execution.execution_time_ms or 0

            # slow but correct → system design issue
            if execution.success and exec_time > 200:
                return PerformanceDimensionType.SYSTEM_DESIGN

        # =====================================================
        # FALLBACK HEURISTICS (important for robustness)
        # =====================================================

        # If execution failed but no clear type → assume technical issue
        if execution and not execution.success:
            return PerformanceDimensionType.TECHNICAL_DEPTH

        # =====================================================
        # DEFAULT
        # =====================================================

        return None
