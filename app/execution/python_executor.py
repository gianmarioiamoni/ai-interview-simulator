# app/execution/python_executor.py

import time
import traceback

from domain.contracts.question import Question
from domain.contracts.execution_result import (
    ExecutionResult,
    ExecutionType,
    ExecutionStatus,
)


class PythonExecutor:
    # Executes Python coding questions inside a controlled sandbox.

    def execute(self, question: Question, code: str) -> ExecutionResult:

        start = time.time()

        try:

            local_env = {}

            exec(code, {}, local_env)

            duration = int((time.time() - start) * 1000)

            return ExecutionResult(
                question_id=question.id,
                execution_type=ExecutionType.CODING,
                status=ExecutionStatus.SUCCESS,
                success=True,
                output=str(local_env),
                passed_tests=0,
                total_tests=0,
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
