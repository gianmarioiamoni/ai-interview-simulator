# app/execution/python_executor.py

import time
import traceback
import signal
import ast
import logging
from typing import Any

from domain.contracts.question import Question
from domain.contracts.execution_result import (
    ExecutionResult,
    ExecutionType,
    ExecutionStatus,
)
from domain.contracts.test_case import TestCase


logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutException("Execution timed out")


class PythonExecutor:

    TIMEOUT_SECONDS = 2

    SAFE_BUILTINS = {
        "range": range,
        "len": len,
        "print": print,
        "str": str,
        "int": int,
        "float": float,
        "list": list,
        "dict": dict,
        "set": set,
        "min": min,
        "max": max,
        "sum": sum,
        "abs": abs,
        "enumerate": enumerate,
    }

    # =========================================================
    # MAIN EXECUTION
    # =========================================================

    def execute(self, question: Question, code: str) -> ExecutionResult:

        start = time.time()

        logger.info(f"Executing coding question: {question.id}")

        try:

            local_env: dict[str, Any] = {}

            safe_globals = {"__builtins__": self.SAFE_BUILTINS}

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.TIMEOUT_SECONDS)

            exec(code, safe_globals, local_env)

            signal.alarm(0)

            logger.debug(f"Local env keys: {list(local_env.keys())}")

            visible_passed = 0
            visible_total = 0

            hidden_passed = 0
            hidden_total = 0

            if question.visible_tests:
                visible_passed, visible_total = self.run_tests(
                    local_env,
                    question.visible_tests,
                )

            if question.hidden_tests:
                hidden_passed, hidden_total = self.run_tests(
                    local_env,
                    question.hidden_tests,
                )

            passed_tests = visible_passed + hidden_passed
            total_tests = visible_total + hidden_total

            duration = int((time.time() - start) * 1000)

            success = passed_tests == total_tests if total_tests > 0 else True

            status = (
                ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED_TESTS
            )

            output = (
                f"Visible tests: {visible_passed}/{visible_total}\n"
                f"Hidden tests: {hidden_passed}/{hidden_total}"
            )

            logger.info(output)

            return ExecutionResult(
                question_id=question.id,
                execution_type=ExecutionType.CODING,
                status=status,
                success=success,
                output=output,
                passed_tests=passed_tests,
                total_tests=total_tests,
                execution_time_ms=duration,
            )

        except TimeoutException:

            logger.error("Execution timeout")

            return ExecutionResult(
                question_id=question.id,
                execution_type=ExecutionType.CODING,
                status=ExecutionStatus.TIMEOUT,
                success=False,
                error="Execution exceeded time limit",
            )

        except SyntaxError as e:

            logger.error(f"Syntax error: {e}")

            return ExecutionResult(
                question_id=question.id,
                execution_type=ExecutionType.CODING,
                status=ExecutionStatus.SYNTAX_ERROR,
                success=False,
                error=str(e),
            )

        except Exception as e:

            logger.error(traceback.format_exc())

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

        passed = 0
        total = len(test_cases)

        functions = [
            v for v in local_env.values() if callable(v) and hasattr(v, "__name__")
        ]

        if not functions:

            logger.error("No candidate function found")

            return 0, total

        candidate_function = functions[0]

        logger.info(f"Testing function: {candidate_function.__name__}")

        for test in test_cases:

            try:

                parsed_input = ast.literal_eval(test.input)

                if isinstance(parsed_input, tuple):
                    result = candidate_function(*parsed_input)
                else:
                    result = candidate_function(parsed_input)

                if str(result) == test.expected_output:
                    passed += 1

            except Exception:

                logger.error(
                    f"Test failed for input {test.input}\n{traceback.format_exc()}"
                )

        return passed, total
