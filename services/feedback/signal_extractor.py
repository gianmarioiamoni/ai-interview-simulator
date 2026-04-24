# services/feedback/signal_extractor.py

from collections import defaultdict
from typing import Dict, Optional

from domain.contracts.execution.execution_result import ExecutionResult
from domain.contracts.execution.test_execution_result import TestStatus
from domain.contracts.feedback.error_type import ErrorType
from domain.contracts.shared.performance_dimension_type import (
    PerformanceDimensionType,
)

from services.feedback.dimension_mapper import FeedbackDimensionMapper


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
        # 1. ERROR TYPE → DIMENSION (PRIMARY SIGNAL)
        # -----------------------------------------------------

        mapped_dimension = FeedbackDimensionMapper.map(error_type, execution)

        if mapped_dimension:
            signals[mapped_dimension.value] += 0.6

        # -----------------------------------------------------
        # 2. TEST-LEVEL SIGNALS
        # -----------------------------------------------------

        failed = 0
        total = execution.total_tests or 0

        for t in execution.test_results:

            if t.status == TestStatus.FAILED:
                failed += 1
                signals[PerformanceDimensionType.PROBLEM_SOLVING.value] += 0.2

            elif t.status == TestStatus.ERROR:
                signals[PerformanceDimensionType.TECHNICAL_DEPTH.value] += 0.3

        # -----------------------------------------------------
        # 3. FAILURE RATIO BOOST
        # -----------------------------------------------------

        if total > 0:
            failure_ratio = failed / total

            signals[PerformanceDimensionType.PROBLEM_SOLVING.value] += (
                failure_ratio * 0.4
            )

        # -----------------------------------------------------
        # 4. PERFORMANCE SIGNAL
        # -----------------------------------------------------

        if execution.execution_time_ms and execution.execution_time_ms > 200:
            signals[PerformanceDimensionType.SYSTEM_DESIGN.value] += 0.3

        # -----------------------------------------------------
        # 5. CLAMP VALUES [0, 1]
        # -----------------------------------------------------

        return {k: min(1.0, round(v, 2)) for k, v in signals.items() if v > 0}
