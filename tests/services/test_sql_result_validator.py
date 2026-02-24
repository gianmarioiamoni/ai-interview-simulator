# tests/services/test_sql_result_validator.py

from services.sql_engine.sql_result_validator import (
    SQLResultValidator,
)


def test_equal_rows_different_order():
    validator = SQLResultValidator()

    expected = [("Alice",), ("Bob",)]
    actual = [("Bob",), ("Alice",)]

    assert validator.validate(expected, actual) is True


def test_not_equal_rows():
    validator = SQLResultValidator()

    expected = [("Alice",)]
    actual = [("Bob",)]

    assert validator.validate(expected, actual) is False


def test_duplicate_rows_preserved():
    validator = SQLResultValidator()

    expected = [("Alice",), ("Alice",)]
    actual = [("Alice",), ("Alice",)]

    assert validator.validate(expected, actual) is True


def test_duplicate_rows_mismatch():
    validator = SQLResultValidator()

    expected = [("Alice",), ("Alice",)]
    actual = [("Alice",)]

    assert validator.validate(expected, actual) is False
