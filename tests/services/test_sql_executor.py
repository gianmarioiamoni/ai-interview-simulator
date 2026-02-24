# tests/services/test_sql_executor.py

from unittest.mock import MagicMock, patch

from services.sql_engine.sql_database import SQLDatabase
from services.sql_engine.sql_executor import SQLExecutor


def test_successful_select_query():
    db = SQLDatabase()
    executor = SQLExecutor()

    output = executor.execute(
        db.connection,
        "SELECT name FROM employees WHERE salary > 80000"
    )

    assert output.success is True
    assert ("Alice",) in output.rows
    assert "name" in output.columns


def test_sql_syntax_error():
    db = SQLDatabase()
    executor = SQLExecutor()

    output = executor.execute(
        db.connection,
        "SELEC name FROM employees"  # typo
    )

    assert output.success is False
    assert output.error is not None


def test_runtime_error_table_not_found():
    db = SQLDatabase()
    executor = SQLExecutor()

    output = executor.execute(
        db.connection,
        "SELECT * FROM non_existing_table"
    )

    assert output.success is False
    assert "no such table" in output.error.lower()


def test_insert_query_commit_branch():
    db = SQLDatabase()
    executor = SQLExecutor()

    output = executor.execute(
        db.connection, "INSERT INTO departments (id, name) VALUES (4, 'Marketing')"
    )

    assert output.success is True
    assert output.rows == []
    assert output.columns == []


def test_generic_exception_branch():
    db = SQLDatabase()
    executor = SQLExecutor()

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("Unexpected failure")

    with patch(
        "services.sql_engine.sql_executor.SQLExecutor._get_cursor",
        return_value=mock_cursor,
    ):
        output = executor.execute(db.connection, "SELECT * FROM employees")

        assert output.success is False
        assert "Unexpected failure" in output.error
