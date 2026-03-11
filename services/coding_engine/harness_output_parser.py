# services/coding_engine/harness_output_parser.py

from domain.contracts.execution_result import (
    ExecutionResult,
    ExecutionType,
    ExecutionStatus,
)


class HarnessOutputParser:

    RESULT_MARKER = "__RESULT__"
    VISIBLE_MARKER = "__VISIBLE__"
    HIDDEN_MARKER = "__HIDDEN__"

    def parse(self, question_id: str, raw) -> ExecutionResult:

        visible_passed = 0
        visible_total = 0
        hidden_passed = 0
        hidden_total = 0

        stdout = raw.stdout or ""

        for line in stdout.splitlines():

            if line.startswith(self.VISIBLE_MARKER):

                try:
                    _, passed, total = line.split(":")
                    visible_passed = int(passed)
                    visible_total = int(total)
                except Exception:
                    pass

            elif line.startswith(self.HIDDEN_MARKER):

                try:
                    _, passed, total = line.split(":")
                    hidden_passed = int(passed)
                    hidden_total = int(total)
                except Exception:
                    pass

        total_passed = visible_passed + hidden_passed
        total_tests = visible_total + hidden_total

        # -----------------------------------------------------
        # Determine execution status
        # -----------------------------------------------------

        if total_tests == 0:

            status = ExecutionStatus.INTERNAL_ERROR
            success = False
            error = "No tests detected in harness output"

        elif total_passed == total_tests:

            status = ExecutionStatus.SUCCESS
            success = True
            error = None

        else:

            status = ExecutionStatus.FAILED_TESTS
            success = False
            error = "Some tests failed"

        return ExecutionResult(
            question_id=question_id,
            execution_type=ExecutionType.CODING,
            status=status,
            success=success,
            output=stdout,
            error=error,
            passed_tests=total_passed,
            total_tests=total_tests,
            execution_time_ms=raw.execution_time_ms,
        )
