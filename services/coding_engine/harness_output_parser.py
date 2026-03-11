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

        for line in raw.stdout.splitlines():

            if line.startswith(self.VISIBLE_MARKER):

                _, passed, total = line.split(":")
                visible_passed = int(passed)
                visible_total = int(total)

            elif line.startswith(self.HIDDEN_MARKER):

                _, passed, total = line.split(":")
                hidden_passed = int(passed)
                hidden_total = int(total)

        total_passed = visible_passed + hidden_passed
        total_tests = visible_total + hidden_total

        if total_passed == total_tests:

            status = ExecutionStatus.SUCCESS
            success = True

        elif total_passed > 0:

            status = ExecutionStatus.FAILED_TESTS
            success = False

        else:

            status = ExecutionStatus.FAILED_TESTS
            success = False

        return ExecutionResult(
            question_id=question_id,
            execution_type=ExecutionType.CODING,
            status=status,
            success=success,
            output=raw.stdout,
            passed_tests=total_passed,
            total_tests=total_tests,
            execution_time_ms=raw.execution_time_ms,
        )
