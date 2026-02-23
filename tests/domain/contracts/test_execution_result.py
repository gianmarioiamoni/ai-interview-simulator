# tests/domain/contracts/test_execution_result.py

import pytest
from pydantic import ValidationError

from domain.contracts.execution_result import (
    ExecutionResult,
    ExecutionType,
)


def test_execution_result_success_valid() -> None:
    result = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        success=True,
        output="42",
    )

    assert result.success is True
    assert result.error is None


def test_execution_result_failure_valid() -> None:
    result = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.DATABASE,
        success=False,
        error="Syntax error",
    )

    assert result.success is False
    assert result.error == "Syntax error"


def test_execution_result_invalid_success_with_error() -> None:
    with pytest.raises(ValidationError):
        ExecutionResult(
            question_id="q1",
            execution_type=ExecutionType.CODING,
            success=True,
            error="Should not exist",
        )


def test_execution_result_invalid_failure_without_error() -> None:
    with pytest.raises(ValidationError):
        ExecutionResult(
            question_id="q1",
            execution_type=ExecutionType.DATABASE,
            success=False,
        )


def test_execution_result_is_frozen() -> None:
    result = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        success=True,
    )

    with pytest.raises(ValidationError):
        result.success = False
