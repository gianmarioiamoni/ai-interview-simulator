# services/execution_analysis/execution_analyzer.py

from typing import Optional

from domain.contracts.execution_result import ExecutionResult, ExecutionStatus
from domain.contracts.test_execution_result import TestStatus
from domain.contracts.feedback.feedback.error_type import ErrorType


class ExecutionAnalysis:

    def __init__(
        self,
        has_global_runtime_error: bool,
        has_test_runtime_errors: bool,
        has_logic_failures: bool,
        primary_error: Optional[str],
        error_type: ErrorType = ErrorType.UNKNOWN,
    ):
        self.has_global_runtime_error = has_global_runtime_error
        self.has_test_runtime_errors = has_test_runtime_errors
        self.has_logic_failures = has_logic_failures
        self.primary_error = primary_error
        self.error_type = error_type


class ExecutionAnalyzer:

    def analyze(self, execution: ExecutionResult) -> ExecutionAnalysis:

        if not execution:
            return ExecutionAnalysis(False, False, False, None)

        error = execution.error or ""

        # ---------------------------------------------------------
        # SIGNATURE ERROR
        # ---------------------------------------------------------

        if error and "Invalid signature" in error:
            return ExecutionAnalysis(
                has_global_runtime_error=False,
                has_test_runtime_errors=False,
                has_logic_failures=True,
                primary_error=error,
                error_type=ErrorType.SIGNATURE,
            )

        # ---------------------------------------------------------
        # SYNTAX ERROR
        # ---------------------------------------------------------

        if execution.status == ExecutionStatus.SYNTAX_ERROR:
            return ExecutionAnalysis(
                has_global_runtime_error=True,
                has_test_runtime_errors=False,
                has_logic_failures=False,
                primary_error=error,
                error_type=ErrorType.SYNTAX,
            )

        # ---------------------------------------------------------
        # RUNTIME ERROR (GLOBAL)
        # ---------------------------------------------------------

        if execution.status == ExecutionStatus.RUNTIME_ERROR:
            return ExecutionAnalysis(
                has_global_runtime_error=True,
                has_test_runtime_errors=False,
                has_logic_failures=False,
                primary_error=error,
                error_type=ErrorType.RUNTIME,
            )

        # ---------------------------------------------------------
        # TEST ANALYSIS
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

        # ---------------------------------------------------------
        # ERROR TYPE DERIVATION
        # ---------------------------------------------------------

        if has_test_runtime_errors:
            error_type = ErrorType.RUNTIME

        elif has_logic_failures:
            error_type = ErrorType.LOGIC

        else:
            error_type = ErrorType.UNKNOWN

        return ExecutionAnalysis(
            has_global_runtime_error=False,
            has_test_runtime_errors=has_test_runtime_errors,
            has_logic_failures=has_logic_failures,
            primary_error=primary_error,
            error_type=error_type,
        )
