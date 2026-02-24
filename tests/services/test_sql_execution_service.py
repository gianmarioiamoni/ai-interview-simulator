# tests/services/test_sql_execution_service.py

from services.sql_engine.sql_database import SQLDatabase
from services.sql_engine.sql_execution_service import SQLExecutionService
from domain.contracts.execution_result import ExecutionStatus


def test_successful_query_validation():
    db = SQLDatabase()
    service = SQLExecutionService()

    query = "SELECT name FROM employees WHERE salary > 80000"
    expected = [("Alice",)]

    result = service.execute(
        question_id="q1",
        connection=db.connection,
        query=query,
        expected_rows=expected,
    )

    assert result.success is True
    assert result.status == ExecutionStatus.SUCCESS


def test_failed_validation():
    db = SQLDatabase()
    service = SQLExecutionService()

    query = "SELECT name FROM employees WHERE salary > 80000"
    expected = [("Bob",)]  # wrong expectation

    result = service.execute(
        question_id="q1",
        connection=db.connection,
        query=query,
        expected_rows=expected,
    )

    assert result.success is False
    assert result.status == ExecutionStatus.FAILED_TESTS


def test_sql_syntax_error():
    db = SQLDatabase()
    service = SQLExecutionService()

    result = service.execute(
        question_id="q1",
        connection=db.connection,
        query="SELEC name FROM employees",
        expected_rows=[],
    )

    assert result.success is False
    assert result.status == ExecutionStatus.SYNTAX_ERROR


def test_sql_runtime_error():
    db = SQLDatabase()
    service = SQLExecutionService()

    result = service.execute(
        question_id="q1",
        connection=db.connection,
        query="SELECT * FROM non_existing_table",
        expected_rows=[],
    )

    assert result.success is False
    assert result.status == ExecutionStatus.RUNTIME_ERROR
