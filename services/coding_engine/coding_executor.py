# services/coding_engine/coding_executor.py

from domain.contracts.question import Question
from domain.contracts.execution_result import (
    ExecutionResult,
    ExecutionType,
    ExecutionStatus,
)

from services.coding_engine.execution_sandbox import ExecutionSandbox
from services.coding_engine.test_case_runner import TestCaseRunner
from services.coding_engine.test_case_adapter import TestCaseAdapter
from services.coding_engine.harness_output_parser import HarnessOutputParser


class CodingExecutor:

    def __init__(
        self,
        sandbox: ExecutionSandbox | None = None,
        runner: TestCaseRunner | None = None,
        parser: HarnessOutputParser | None = None,
    ) -> None:

        self._sandbox = sandbox or ExecutionSandbox()
        self._runner = runner or TestCaseRunner()
        self._parser = parser or HarnessOutputParser()
        self._adapter = TestCaseAdapter()

    # ---------------------------------------------------------
    # Execute coding question
    # ---------------------------------------------------------

    def execute(
        self,
        question: Question,
        user_code: str,
    ) -> ExecutionResult:

        # -----------------------------------------------------
        # Build harness
        # -----------------------------------------------------

        visible_tests = question.visible_tests or []
        hidden_tests = self._adapter.to_coding_test_cases(question.hidden_tests or [])

        harness = self._runner.build_harness(
            user_code=user_code,
            visible_tests=visible_tests,
            hidden_tests=hidden_tests,
            function_name=question.function_name or "solution",
        )

        # -----------------------------------------------------
        # Execute in sandbox
        # -----------------------------------------------------

        raw = self._sandbox.execute(harness)
        print("=== RAW STDOUT ===")
        print(raw.stdout)
        print("==================")

        # -----------------------------------------------------
        # Timeout
        # -----------------------------------------------------

        if raw.timeout:

            return ExecutionResult(
                question_id=question.id,
                execution_type=ExecutionType.CODING,
                status=ExecutionStatus.TIMEOUT,
                success=False,
                error="Execution timed out",
                output=raw.stdout,
                execution_time_ms=raw.execution_time_ms,
            )

        # -----------------------------------------------------
        # Syntax / runtime error before tests
        # -----------------------------------------------------

        if raw.returncode != 0 and "__RESULT__" not in (raw.stdout or ""):

            return ExecutionResult(
                question_id=question.id,
                execution_type=ExecutionType.CODING,
                status=ExecutionStatus.RUNTIME_ERROR,
                success=False,
                error=raw.stderr or "Runtime error",
                output=raw.stdout,
                execution_time_ms=raw.execution_time_ms,
            )

        # -----------------------------------------------------
        # Parse harness output
        # -----------------------------------------------------

        return self._parser.parse(question.id, raw)
