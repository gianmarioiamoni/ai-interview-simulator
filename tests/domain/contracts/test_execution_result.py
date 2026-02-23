# Tests for updated ExecutionResult contract

import pytest
from pydantic import ValidationError

from domain.contracts.execution_result import (
    ExecutionResult,
    ExecutionType,
    ExecutionStatus,
)


# -------------------------
# SUCCESS CASES
# -------------------------


def test_success_execution_result():
    result = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        status=ExecutionStatus.SUCCESS,
        success=True,
        output="All tests passed",
        passed_tests=3,
        total_tests=3,
        execution_time_ms=120,
    )

    assert result.success is True
    assert result.status == ExecutionStatus.SUCCESS
    assert result.error is None
    assert result.passed_tests == 3
    assert result.total_tests == 3


def test_failed_tests_execution_result():
    result = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        status=ExecutionStatus.FAILED_TESTS,
        success=False,
        output="Test 2 failed",
        error="AssertionError",
        passed_tests=2,
        total_tests=3,
        execution_time_ms=150,
    )

    assert result.success is False
    assert result.status == ExecutionStatus.FAILED_TESTS
    assert result.error == "AssertionError"


def test_timeout_execution_result():
    result = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        status=ExecutionStatus.TIMEOUT,
        success=False,
        output="",
        error="Execution timed out",
        execution_time_ms=5000,
    )

    assert result.status == ExecutionStatus.TIMEOUT
    assert result.success is False


def test_database_execution_result_success():
    result = ExecutionResult(
        question_id="sql1",
        execution_type=ExecutionType.DATABASE,
        status=ExecutionStatus.SUCCESS,
        success=True,
        output="[(1, 'Alice')]",
        passed_tests=1,
        total_tests=1,
        execution_time_ms=50,
    )

    assert result.execution_type == ExecutionType.DATABASE


# -------------------------
# VALIDATION ERRORS
# -------------------------


def test_status_success_must_match_success_true():
    with pytest.raises(ValidationError):
        ExecutionResult(
            question_id="q1",
            execution_type=ExecutionType.CODING,
            status=ExecutionStatus.SUCCESS,
            success=False,
            output="",
            error="Some error",
        )


def test_success_true_requires_status_success():
    with pytest.raises(ValidationError):
        ExecutionResult(
            question_id="q1",
            execution_type=ExecutionType.CODING,
            status=ExecutionStatus.RUNTIME_ERROR,
            success=True,
            output="",
        )


def test_success_true_cannot_have_error():
    with pytest.raises(ValidationError):
        ExecutionResult(
            question_id="q1",
            execution_type=ExecutionType.CODING,
            status=ExecutionStatus.SUCCESS,
            success=True,
            output="OK",
            error="Should not exist",
        )


def test_success_false_requires_error():
    with pytest.raises(ValidationError):
        ExecutionResult(
            question_id="q1",
            execution_type=ExecutionType.CODING,
            status=ExecutionStatus.RUNTIME_ERROR,
            success=False,
            output="",
        )


def test_passed_tests_cannot_exceed_total_tests():
    with pytest.raises(ValidationError):
        ExecutionResult(
            question_id="q1",
            execution_type=ExecutionType.CODING,
            status=ExecutionStatus.FAILED_TESTS,
            success=False,
            output="",
            error="Failed",
            passed_tests=5,
            total_tests=3,
        )


def test_negative_execution_time_not_allowed():
    with pytest.raises(ValidationError):
        ExecutionResult(
            question_id="q1",
            execution_type=ExecutionType.CODING,
            status=ExecutionStatus.SUCCESS,
            success=True,
            output="OK",
            execution_time_ms=-10,
        )


# -------------------------
# IMMUTABILITY
# -------------------------


def test_execution_result_is_immutable():
    result = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        status=ExecutionStatus.SUCCESS,
        success=True,
        output="OK",
    )

    with pytest.raises(ValidationError):
        result.output = "Modified"
