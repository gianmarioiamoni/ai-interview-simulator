# app/execution/python_executor.py

import time
import traceback
from typing import Any

from domain.contracts.question import Question
from domain.contracts.execution_result import (
    ExecutionResult,
    ExecutionType,
    ExecutionStatus,
)
from domain.contracts.test_case import TestCase


class PythonExecutor:
    # Executes Python coding questions inside a controlled sandbox
    # and optionally evaluates deterministic test cases.

    def execute(self, question: Question, code: str) -> ExecutionResult:

        start = time.time()

        try:

            local_env: dict[str, Any] = {}

            # ---------------------------------------------------------
            # Execute candidate code
            # ---------------------------------------------------------

            exec(code, {}, local_env)

            # ---------------------------------------------------------
            # Run test cases if available
            # ---------------------------------------------------------

            passed_tests = 0
            total_tests = 0

            if question.test_cases:

                passed_tests, total_tests = self.run_tests(
                    local_env,
                    question.test_cases,
                )

            duration = int((time.time() - start) * 1000)

            success = passed_tests == total_tests if total_tests > 0 else True

            status = (
                ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED_TESTS
            )

            return ExecutionResult(
                question_id=question.id,
                execution_type=ExecutionType.CODING,
                status=status,
                success=success,
                output=f"{passed_tests}/{total_tests} tests passed",
                passed_tests=passed_tests,
                total_tests=total_tests,
                execution_time_ms=duration,
            )

        except SyntaxError as e:

            return ExecutionResult(
                question_id=question.id,
                execution_type=ExecutionType.CODING,
                status=ExecutionStatus.SYNTAX_ERROR,
                success=False,
                error=str(e),
            )

        except Exception:

            return ExecutionResult(
                question_id=question.id,
                execution_type=ExecutionType.CODING,
                status=ExecutionStatus.RUNTIME_ERROR,
                success=False,
                error=traceback.format_exc(),
            )

    # =========================================================
    # TEST RUNNER
    # =========================================================

    def run_tests(
        self,
        local_env: dict[str, Any],
        test_cases: list[TestCase],
    ) -> tuple[int, int]:
        # Executes deterministic test cases against the candidate function.
        # Returns (passed_tests, total_tests).

        passed = 0
        total = len(test_cases)

        # ---------------------------------------------------------
        # Retrieve candidate function
        # ---------------------------------------------------------

        functions = [v for v in local_env.values() if callable(v)]

        if not functions:
            return 0, total

        candidate_function = functions[0]

        # ---------------------------------------------------------
        # Execute tests
        # ---------------------------------------------------------

        for test in test_cases:

            try:

                result = candidate_function(test.input)

                if str(result) == test.expected_output:
                    passed += 1

            except Exception:
                # Test considered failed
                continue

        return passed, total
