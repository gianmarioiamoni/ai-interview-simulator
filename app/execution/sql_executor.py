# app/execution/sql_executor.py

import sqlite3
import time
import traceback

from domain.contracts.question import Question
from domain.contracts.execution_result import (
    ExecutionResult,
    ExecutionType,
    ExecutionStatus,
)


class SQLExecutor:

    def execute(self, question: Question, query: str) -> ExecutionResult:

        start = time.time()

        try:

            conn = sqlite3.connect(":memory:")
            cursor = conn.cursor()

            cursor.execute(query)

            rows = cursor.fetchall()

            conn.close()

            duration = int((time.time() - start) * 1000)

            return ExecutionResult(
                question_id=question.id,
                execution_type=ExecutionType.DATABASE,
                status=ExecutionStatus.SUCCESS,
                success=True,
                output=str(rows),
                execution_time_ms=duration,
            )

        except Exception:

            return ExecutionResult(
                question_id=question.id,
                execution_type=ExecutionType.DATABASE,
                status=ExecutionStatus.RUNTIME_ERROR,
                success=False,
                error=traceback.format_exc(),
            )
