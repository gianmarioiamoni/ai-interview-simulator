import sqlite3
import time
import traceback
import logging

from domain.contracts.question import Question
from domain.contracts.execution_result import (
    ExecutionResult,
    ExecutionType,
    ExecutionStatus,
)

logger = logging.getLogger(__name__)


class SQLExecutor:

    def execute(self, question: Question, query: str) -> ExecutionResult:

        logger.info(f"SQL query received:\n{query}")

        start = time.time()

        try:

            connection = sqlite3.connect(":memory:")
            cursor = connection.cursor()

            # eventual setup schema if present in the question
            if hasattr(question, "schema_sql") and question.schema_sql:
                cursor.executescript(question.schema_sql)

            cursor.execute(query)

            rows = cursor.fetchall()

            connection.close()

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
