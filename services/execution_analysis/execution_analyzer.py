# services/execution_analysis/execution_analyzer.py

from typing import Optional

from domain.contracts.execution_result import ExecutionResult, ExecutionStatus
from domain.contracts.test_execution_result import TestStatus


class ExecutionAnalysis:

    def __init__(
        self,
        has_global_runtime_error: bool,
        has_test_runtime_errors: bool,
        has_logic_failures: bool,
        primary_error: Optional[str],
    ):
        self.has_global_runtime_error = has_global_runtime_error
        self.has_test_runtime_errors = has_test_runtime_errors
        self.has_logic_failures = has_logic_failures
        self.primary_error = primary_error


class ExecutionAnalyzer:

    def analyze(self, execution: ExecutionResult) -> ExecutionAnalysis:

        if not execution:
            return ExecutionAnalysis(False, False, False, None)

        # 🔥 FIX: signature error → logic failure
        if execution.error and "Invalid signature" in execution.error:
            return ExecutionAnalysis(
                has_global_runtime_error=False,
                has_test_runtime_errors=False,
                has_logic_failures=True,
                primary_error=execution.error,
            )

        # ---------------------------------------------------------

        if execution.status == ExecutionStatus.RUNTIME_ERROR:
            return ExecutionAnalysis(
                has_global_runtime_error=True,
                has_test_runtime_errors=False,
                has_logic_failures=False,
                primary_error=execution.error,
            )

        # ---------------------------------------------------------

        has_test_runtime_errors = False
        has_logic_failures = False
        primary_error = None

        for t in execution.test_results:

            if t.status == TestStatus.ERROR:
                has_test_runtime_errors = True
                if not primary_error:
                    primary_error = t.error

            elif t.status == TestStatus.FAILED:
                has_logic_failures = True

        return ExecutionAnalysis(
            has_global_runtime_error=False,
            has_test_runtime_errors=has_test_runtime_errors,
            has_logic_failures=has_logic_failures,
            primary_error=primary_error,
        )
