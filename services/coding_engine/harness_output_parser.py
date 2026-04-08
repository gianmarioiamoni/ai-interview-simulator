# services/coding_engine/harness_output_parser.py

import json
from typing import List

from domain.contracts.execution_result import (
    ExecutionResult,
    ExecutionType,
    ExecutionStatus,
)
from domain.contracts.test_execution_result import (
    TestExecutionResult,
    TestStatus,
    TestType,
)


class HarnessOutputParser:

    RESULT_MARKER = "__RESULT__"
    VISIBLE_MARKER = "__VISIBLE__"
    HIDDEN_MARKER = "__HIDDEN__"
    TEST_RESULT_MARKER = "__TEST_RESULT__"

    def parse(self, question_id: str, raw) -> ExecutionResult:

        visible_passed = 0
        visible_total = 0
        hidden_passed = 0
        hidden_total = 0

        test_results: List[TestExecutionResult] = []

        stdout = raw.stdout or ""

        for line in stdout.splitlines():

            if line.startswith(self.TEST_RESULT_MARKER):

                try:
                    payload = line.replace(f"{self.TEST_RESULT_MARKER}:", "")
                    data = json.loads(payload)

                    test_results.append(
                        TestExecutionResult(
                            id=data.get("id"),
                            type=TestType(data.get("type")),
                            status=TestStatus(data.get("status")),
                            expected=data.get("expected"),
                            actual=data.get("actual"),
                            error=data.get("error"),
                            args=data.get("args", []),
                            kwargs=data.get("kwargs", {}),
                        )
                    )

                except Exception:
                    continue

            elif line.startswith(self.VISIBLE_MARKER):
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

        # =========================================================
        # 🔥 FIX: USE STRUCTURED TESTS IF AVAILABLE
        # =========================================================

        if test_results:
            total_tests = len(test_results)
            total_passed = sum(1 for t in test_results if t.status == TestStatus.PASSED)
        else:
            total_passed = visible_passed + hidden_passed
            total_tests = visible_total + hidden_total

        # =========================================================
        # 🔥 FIX: ERROR CLASSIFICATION
        # =========================================================

        signature_error = next(
            (
                t.error
                for t in test_results
                if t.error and "Invalid signature" in t.error
            ),
            None,
        )

        has_runtime_errors = any(
            t.status == TestStatus.ERROR and "Invalid signature" not in (t.error or "")
            for t in test_results
        )

        # =========================================================
        # STATUS
        # =========================================================

        if total_tests == 0:
            status = ExecutionStatus.INTERNAL_ERROR
            success = False
            error = "No tests detected"

        elif signature_error:
            # Treat as FAILED_TESTS, not runtime
            status = ExecutionStatus.FAILED_TESTS
            success = False
            error = signature_error

        elif has_runtime_errors:
            status = ExecutionStatus.RUNTIME_ERROR
            success = False
            error = next((t.error for t in test_results if t.error), "Runtime error")

        elif total_passed == total_tests:
            status = ExecutionStatus.SUCCESS
            success = True
            error = None

        else:
            status = ExecutionStatus.FAILED_TESTS
            success = False
            error = "Some tests failed"

        # =========================================================

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
            test_results=test_results,
        )
