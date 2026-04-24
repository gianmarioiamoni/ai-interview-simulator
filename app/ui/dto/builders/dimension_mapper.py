# services/feedback/dimension_mapper.py

from domain.contracts.feedback.error_type import ErrorType
from domain.contracts.shared.performance_dimension_type import (
    PerformanceDimensionType,
)


class FeedbackDimensionMapper:

    @staticmethod
    def map(error_type: ErrorType, execution=None):

        # -----------------------------------------------------
        # SQL / LOGIC
        # -----------------------------------------------------

        if error_type == ErrorType.LOGIC:
            return PerformanceDimensionType.PROBLEM_SOLVING

        # -----------------------------------------------------
        # RUNTIME / SYNTAX
        # -----------------------------------------------------

        if error_type in (
            ErrorType.RUNTIME,
            ErrorType.SYNTAX,
            ErrorType.SIGNATURE,
        ):
            return PerformanceDimensionType.TECHNICAL_DEPTH

        # -----------------------------------------------------
        # PERFORMANCE (basic heuristic)
        # -----------------------------------------------------

        if execution and execution.execution_time_ms:

            if execution.execution_time_ms > 200:
                return PerformanceDimensionType.SYSTEM_DESIGN

        # -----------------------------------------------------
        # DEFAULT
        # -----------------------------------------------------

        return None