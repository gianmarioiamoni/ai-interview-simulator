# app/execution/sql_executor.py

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

        connection = None

        try:

            connection = sqlite3.connect(":memory:")
            cursor = connection.cursor()

            # ---------------------------------------------------------
            # Load schema if provided
            # ---------------------------------------------------------

            if hasattr(question, "schema_sql") and question.schema_sql:
                cursor.executescript(question.schema_sql)

            # ---------------------------------------------------------
            # Load seed data if provided
            # ---------------------------------------------------------

            if hasattr(question, "seed_data_sql") and question.seed_data_sql:
                cursor.executescript(question.seed_data_sql)

            # ---------------------------------------------------------
            # Execute user query
            # ---------------------------------------------------------

            cursor.execute(query)

            rows = cursor.fetchall()

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

        finally:

            if connection:
                connection.close()
