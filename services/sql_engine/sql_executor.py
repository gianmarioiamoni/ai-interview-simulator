# services/sql_engine/sql_executor.py

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

from services.sql_engine.sql_evaluator import SQLEvaluator

logger = logging.getLogger(__name__)


class SQLExecutor:

    def __init__(self):
        self._evaluator = SQLEvaluator()

    def execute(self, question: Question, query: str) -> ExecutionResult:

        start = time.time()

        try:

            conn = sqlite3.connect(":memory:")
            cursor = conn.cursor()

            # ---------------------------------------------------------
            # Schema
            # ---------------------------------------------------------

            if question.db_schema:
                cursor.executescript(question.db_schema)

            # ---------------------------------------------------------
            # Seed
            # ---------------------------------------------------------

            if question.db_seed_data:
                cursor.executescript(question.db_seed_data)

            # ---------------------------------------------------------
            # Evaluation with reference
            # ---------------------------------------------------------

            if question.reference_solution:

                success, candidate_rows, reference_rows = self._evaluator.evaluate(
                    cursor,
                    candidate_query=query,
                    reference_query=question.reference_solution,
                    ordered=question.expected_ordered,
                )

                duration = int((time.time() - start) * 1000)
                conn.close()

                if success:
                    status = ExecutionStatus.SUCCESS
                    error = None
                    passed_tests = 1
                else:
                    status = ExecutionStatus.FAILED_TESTS
                    error = (
                        "Query results differ from reference solution\n"
                        f"Expected: {reference_rows}\n"
                        f"Got: {candidate_rows}"
                    )
                    passed_tests = 0

                return ExecutionResult(
                    question_id=question.id,
                    execution_type=ExecutionType.DATABASE,
                    status=status,
                    success=success,
                    output=str(candidate_rows),
                    error=error,
                    execution_time_ms=duration,
                    passed_tests=passed_tests,
                    total_tests=1,
                )

            # ---------------------------------------------------------
            # No reference → best effort execution
            # ---------------------------------------------------------

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
                error=None,
                execution_time_ms=duration,
                passed_tests=1,
                total_tests=1,
            )

        except Exception:

            return ExecutionResult(
                question_id=question.id,
                execution_type=ExecutionType.DATABASE,
                status=ExecutionStatus.RUNTIME_ERROR,
                success=False,
                error=traceback.format_exc(),
                passed_tests=0,
                total_tests=1,
            )
