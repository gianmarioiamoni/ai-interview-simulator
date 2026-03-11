# services/coding_engine/coding_executor.py

from domain.contracts.question import Question
from domain.contracts.execution_result import ExecutionResult

from services.coding_engine.execution_sandbox import ExecutionSandbox
from services.coding_engine.test_case_runner import TestCaseRunner
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

    def execute(
        self,
        question: Question,
        user_code: str,
    ) -> ExecutionResult:

        harness = self._runner.build_harness(
            user_code=user_code,
            visible_tests=question.visible_tests,
            hidden_tests=question.hidden_tests,
        )

        raw = self._sandbox.execute(harness)

        # timeout
        if raw.timeout:

            return ExecutionResult(
                question_id=question.id,
                execution_type="coding",
                status="timeout",
                success=False,
                error="Execution timed out",
            )

        # syntax error
        if raw.returncode != 0 and "__RESULT__" not in raw.stdout:

            return ExecutionResult(
                question_id=question.id,
                execution_type="coding",
                status="runtime_error",
                success=False,
                output=raw.stdout,
                error=raw.stderr,
            )

        # parse harness output
        return self._parser.parse(question.id, raw)
