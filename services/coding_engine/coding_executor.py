# services/coding_engine/coding_executor.py

# CodingExecutor
#
# Responsibility:
# Orchestrates test harness generation and sandbox execution.
# Interprets raw execution output and builds structured ExecutionResult.

from domain.contracts.execution_result import (
    ExecutionResult,
    ExecutionType,
    ExecutionStatus,
)
from domain.contracts.coding_test_case import CodingTestCase

from services.coding_engine.execution_sandbox import ExecutionSandbox
from services.coding_engine.test_case_runner import TestCaseRunner


class CodingExecutor:
    def __init__(
        self,
        sandbox: ExecutionSandbox | None = None,
        runner: TestCaseRunner | None = None,
    ) -> None:
        self._sandbox = sandbox or ExecutionSandbox()
        self._runner = runner or TestCaseRunner()

    def execute(
        self,
        question_id: str,
        user_code: str,
        function_name: str,
        test_cases: list[CodingTestCase],
    ) -> ExecutionResult:

        harness = self._runner.build_harness(
            user_code=user_code,
            function_name=function_name,
            test_cases=test_cases,
        )

        raw = self._sandbox.execute(harness)

        # Timeout
        if raw.timeout:
            return ExecutionResult(
                question_id=question_id,
                execution_type=ExecutionType.CODING,
                status=ExecutionStatus.TIMEOUT,
                success=False,
                output=raw.stdout,
                error=raw.stderr,
                execution_time_ms=raw.execution_time_ms,
            )

        # Syntax error (Python exit before tests)
        if raw.returncode != 0 and TestCaseRunner.RESULT_MARKER not in raw.stdout:
            error_status = (
                ExecutionStatus.SYNTAX_ERROR 
                if "SyntaxError" in raw.stderr 
                else ExecutionStatus.RUNTIME_ERROR
            )
            return ExecutionResult(
                question_id=question_id,
                execution_type=ExecutionType.CODING,
                status=error_status,
                success=False,
                output=raw.stdout,
                error=raw.stderr,
                execution_time_ms=raw.execution_time_ms,
            )

        # Parse result marker
        marker_line = None
        for line in raw.stdout.splitlines():
            if line.startswith(TestCaseRunner.RESULT_MARKER):
                marker_line = line
                break

        if not marker_line:
            return ExecutionResult(
                question_id=question_id,
                execution_type=ExecutionType.CODING,
                status=ExecutionStatus.INTERNAL_ERROR,
                success=False,
                output=raw.stdout,
                error="Missing result marker",
                execution_time_ms=raw.execution_time_ms,
            )

        _, passed_str, total_str = marker_line.split(":")
        passed = int(passed_str)
        total = int(total_str)

        if passed == total:
            return ExecutionResult(
                question_id=question_id,
                execution_type=ExecutionType.CODING,
                status=ExecutionStatus.SUCCESS,
                success=True,
                output=raw.stdout,
                passed_tests=passed,
                total_tests=total,
                execution_time_ms=raw.execution_time_ms,
            )

        return ExecutionResult(
            question_id=question_id,
            execution_type=ExecutionType.CODING,
            status=ExecutionStatus.FAILED_TESTS,
            success=False,
            output=raw.stdout,
            error="Some tests failed",
            passed_tests=passed,
            total_tests=total,
            execution_time_ms=raw.execution_time_ms,
        )
