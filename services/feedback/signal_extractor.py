# services/feedback/signal_extractor.py

from collections import defaultdict
from typing import Dict, Optional

from domain.contracts.execution.execution_result import ExecutionResult
from domain.contracts.execution.test_execution_result import TestStatus
from domain.contracts.feedback.error_type import ErrorType
from domain.contracts.shared.performance_dimension_type import (
    PerformanceDimensionType,
)


class SignalExtractor:
    # Extracts dimension-level signals from execution results.
    #
    # Output:
    # {
    #     "problem_solving": float,
    #     "technical_depth": float,
    #     "system_design": float
    # }

    def extract(
        self,
        execution: Optional[ExecutionResult],
        error_type: Optional[ErrorType],
    ) -> Dict[str, float]:

        if not execution:
            return {}

        signals = defaultdict(float)

        # -----------------------------------------------------
        # GLOBAL ERROR SIGNALS
        # -----------------------------------------------------

        if execution.status in ["runtime_error", "syntax_error"]:
            signals[PerformanceDimensionType.TECHNICAL_DEPTH.value] += 0.7

        # -----------------------------------------------------
        # TEST-LEVEL SIGNALS
        # -----------------------------------------------------

        failed = 0
        total = execution.total_tests or 0

        for t in execution.test_results:

            if t.status == TestStatus.FAILED:
                failed += 1
                signals[PerformanceDimensionType.PROBLEM_SOLVING.value] += 0.3

            elif t.status == TestStatus.ERROR:
                signals[PerformanceDimensionType.TECHNICAL_DEPTH.value] += 0.4

        # -----------------------------------------------------
        # NORMALIZE BY FAILURE RATIO
        # -----------------------------------------------------

        if total > 0:
            failure_ratio = failed / total

            signals[PerformanceDimensionType.PROBLEM_SOLVING.value] += (
                failure_ratio * 0.5
            )

        # -----------------------------------------------------
        # PERFORMANCE SIGNAL
        # -----------------------------------------------------

        if execution.execution_time_ms and execution.execution_time_ms > 200:
            signals[PerformanceDimensionType.SYSTEM_DESIGN.value] += 0.3

        # -----------------------------------------------------
        # ERROR TYPE BOOST
        # -----------------------------------------------------

        if error_type == ErrorType.LOGIC:
            signals[PerformanceDimensionType.PROBLEM_SOLVING.value] += 0.5

        elif error_type in (
            ErrorType.RUNTIME,
            ErrorType.SYNTAX,
            ErrorType.SIGNATURE,
        ):
            signals[PerformanceDimensionType.TECHNICAL_DEPTH.value] += 0.5

        # -----------------------------------------------------
        # CLAMP VALUES [0, 1]
        # -----------------------------------------------------

        return {k: min(1.0, round(v, 2)) for k, v in signals.items() if v > 0}
