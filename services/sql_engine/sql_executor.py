# services/sql_engine/sql_executor.py

import sqlite3
import time
import traceback

from domain.contracts.question.question import Question
from domain.contracts.execution.execution_result import (
    ExecutionResult,
    ExecutionType,
    ExecutionStatus,
)
from domain.contracts.execution.test_execution_result import (
    TestExecutionResult,
    TestStatus,
    TestType,
)

from services.sql_engine.sql_evaluator import SQLEvaluator

from app.core.logger import get_logger

logger = get_logger(__name__)


class SQLExecutor:

    def __init__(self):
        self._evaluator = SQLEvaluator()

    # ---------------------------------------------------------

    def execute(self, question: Question, query: str) -> ExecutionResult:

        start = time.time()

        try:

            conn = sqlite3.connect(":memory:")
            cursor = conn.cursor()

            # -----------------------------------------------------
            # SCHEMA + DATA
            # -----------------------------------------------------

            if question.db_schema:
                cursor.executescript(question.db_schema)

            if question.db_seed_data:
                cursor.executescript(question.db_seed_data)

            # -----------------------------------------------------
            # MULTI TEST EXECUTION (NEW)
            # -----------------------------------------------------

            test_results = []

            sql_tests = getattr(question, "sql_test_cases", []) or []

            for idx, test in enumerate(sql_tests):

                try:

                    effective_ordered = (
                        test.ordered
                        if test.ordered is not None
                        else question.expected_ordered
                    )

                    success, candidate_rows, expected_rows = self._evaluator.evaluate(
                        cursor,
                        candidate_query=query,
                        reference_query=test.expected_query,
                        ordered=effective_ordered,
                    )

                    status = TestStatus.PASSED if success else TestStatus.FAILED

                    test_results.append(
                        TestExecutionResult(
                            id=idx,
                            type=TestType.VISIBLE,
                            status=status,
                            expected=expected_rows,
                            actual=candidate_rows,
                            error=None,
                        )
                    )

                except Exception as e:

                    test_results.append(
                        TestExecutionResult(
                            id=idx,
                            type=TestType.VISIBLE,
                            status=TestStatus.ERROR,
                            expected=None,
                            actual=None,
                            error=str(e),
                        )
                    )

            # -----------------------------------------------------
            # AGGREGATION
            # -----------------------------------------------------

            total_tests = len(test_results)
            passed_tests = sum(1 for t in test_results if t.status == TestStatus.PASSED)

            success = passed_tests == total_tests and total_tests > 0

            duration = int((time.time() - start) * 1000)
            conn.close()

            status = (
                ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED_TESTS
            )

            error = None

            if not success:
                error = "Test execution failed"

            return ExecutionResult(
                question_id=question.id,
                execution_type=ExecutionType.DATABASE,
                status=status,
                success=success,
                output="",
                error=error if not success else None,
                execution_time_ms=duration,
                passed_tests=passed_tests,
                total_tests=total_tests,
                test_results=test_results,  # 🔥 KEY
            )

        except Exception:

            return ExecutionResult(
                question_id=question.id,
                execution_type=ExecutionType.DATABASE,
                status=ExecutionStatus.RUNTIME_ERROR,
                success=False,
                error=traceback.format_exc(),
                passed_tests=0,
                total_tests=0,
                test_results=[],
            )
