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
from services.execution_analysis.execution_analyzer import ExecutionAnalysis
from infrastructure.config.evaluation import (
    SIGNAL_PRIMARY_ERROR_WEIGHT,
    SIGNAL_FAILED_TEST_PS_WEIGHT,
    SIGNAL_TEST_ERROR_TD_WEIGHT,
    SIGNAL_FAILURE_RATIO_PS_WEIGHT,
    SIGNAL_PERFECT_PS_WEIGHT,
    SIGNAL_PERFECT_TD_WEIGHT,
    SIGNAL_PASS_RATE_PS_WEIGHT,
    SIGNAL_PASS_RATE_THRESHOLD,
    SIGNAL_SLOW_EXEC_SD_WEIGHT,
    SIGNAL_SLOW_EXEC_MS,
)


class SignalExtractor:

    def extract(
        self,
        execution: Optional[ExecutionResult],
        error_type: Optional[ErrorType],
        analysis: Optional[ExecutionAnalysis] = None,
    ) -> Dict[str, float]:

        if not execution or not analysis:
            return {}

        signals = defaultdict(float)

        # -----------------------------------------------------
        # 1. PRIMARY ERROR SIGNAL
        # -----------------------------------------------------

        mapped_dimension = FeedbackDimensionMapper.map(error_type, execution)

        if mapped_dimension:
            signals[mapped_dimension.value] += SIGNAL_PRIMARY_ERROR_WEIGHT

        # -----------------------------------------------------
        # 2. TEST-LEVEL NEGATIVE SIGNALS
        # -----------------------------------------------------

        failed = 0
        total = execution.total_tests or 0

        for t in execution.test_results:

            if t.status == TestStatus.FAILED:
                failed += 1
                signals[PerformanceDimensionType.PROBLEM_SOLVING.value] += SIGNAL_FAILED_TEST_PS_WEIGHT

            elif t.status == TestStatus.ERROR:
                signals[PerformanceDimensionType.TECHNICAL_DEPTH.value] += SIGNAL_TEST_ERROR_TD_WEIGHT

        # -----------------------------------------------------
        # 3. FAILURE RATIO
        # -----------------------------------------------------

        if total > 0:
            failure_ratio = failed / total
            signals[PerformanceDimensionType.PROBLEM_SOLVING.value] += (
                failure_ratio * SIGNAL_FAILURE_RATIO_PS_WEIGHT
            )

        # -----------------------------------------------------
        # 4. POSITIVE SIGNALS
        # -----------------------------------------------------

        if analysis.is_perfect:
            signals[PerformanceDimensionType.PROBLEM_SOLVING.value] += SIGNAL_PERFECT_PS_WEIGHT
            signals[PerformanceDimensionType.TECHNICAL_DEPTH.value] += SIGNAL_PERFECT_TD_WEIGHT

        elif analysis.pass_rate > SIGNAL_PASS_RATE_THRESHOLD:
            signals[PerformanceDimensionType.PROBLEM_SOLVING.value] += SIGNAL_PASS_RATE_PS_WEIGHT

        # -----------------------------------------------------
        # 5. PERFORMANCE SIGNAL
        # -----------------------------------------------------

        if execution.execution_time_ms and execution.execution_time_ms > SIGNAL_SLOW_EXEC_MS:
            signals[PerformanceDimensionType.SYSTEM_DESIGN.value] += SIGNAL_SLOW_EXEC_SD_WEIGHT

        # -----------------------------------------------------
        # 6. CLAMP
        # -----------------------------------------------------

        return {k: min(1.0, round(v, 2)) for k, v in signals.items() if v > 0}
