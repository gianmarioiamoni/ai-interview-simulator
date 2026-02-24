# services/sql_engine/sql_execution_service.py

# SQLExecutionService
#
# Responsibility:
# - Executes SQL query
# - Validates result against expected rows
# - Builds ExecutionResult
# - Distinguishes SQL error types

from domain.contracts.execution_result import (
    ExecutionResult,
    ExecutionType,
    ExecutionStatus,
)

from services.sql_engine.sql_executor import SQLExecutor
from services.sql_engine.sql_result_validator import SQLResultValidator

import sqlite3


class SQLExecutionService:
    def __init__(
        self,
        executor: SQLExecutor | None = None,
        validator: SQLResultValidator | None = None,
    ) -> None:
        self._executor = executor or SQLExecutor()
        self._validator = validator or SQLResultValidator()

    def execute(
        self,
        question_id: str,
        connection: sqlite3.Connection,
        query: str,
        expected_rows: list[tuple],
    ) -> ExecutionResult:

        output = self._executor.execute(connection, query)

        # SQL execution failure
        if not output.success:
            error_message = output.error or ""

            status = (
                ExecutionStatus.SYNTAX_ERROR
                if "syntax" in error_message.lower()
                else ExecutionStatus.RUNTIME_ERROR
            )

            return ExecutionResult(
                question_id=question_id,
                execution_type=ExecutionType.DATABASE,
                status=status,
                success=False,
                output="",
                error=error_message,
            )

        # Validate result
        is_valid = self._validator.validate(
            expected_rows=expected_rows,
            actual_rows=output.rows,
        )

        if not is_valid:
            return ExecutionResult(
                question_id=question_id,
                execution_type=ExecutionType.DATABASE,
                status=ExecutionStatus.FAILED_TESTS,
                success=False,
                output=str(output.rows),
                error="Result validation failed",
            )

        # Success
        return ExecutionResult(
            question_id=question_id,
            execution_type=ExecutionType.DATABASE,
            status=ExecutionStatus.SUCCESS,
            success=True,
            output=str(output.rows),
            error=None,
        )
