# tests/ui/test_summary_block.py

import pytest
from unittest.mock import MagicMock

from app.ui.presenters.feedback.blocks.summary_block import SummaryBlock
from domain.contracts.feedback.quality import Quality
from domain.contracts.execution.execution_result import (
    ExecutionResult,
    ExecutionStatus,
    ExecutionType,
)


def _execution(*, success: bool, passed: int, total: int) -> ExecutionResult:
    return ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        status=ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED_TESTS,
        success=success,
        output="",
        error=None if success else "Some tests failed",
        passed_tests=passed,
        total_tests=total,
        execution_time_ms=10,
        test_results=[],
    )


def _build(*, quality: Quality, execution: ExecutionResult | None, is_coding: bool = True):
    block = SummaryBlock()
    question = MagicMock()
    question.is_coding.return_value = is_coding
    question.is_written.return_value = not is_coding
    result = MagicMock()
    result.question = question
    return block.build(None, result, None, execution, None, quality=quality)


# ---------------------------------------------------------
# All tests pass — full success message
# ---------------------------------------------------------


def test_summary_all_tests_passed_shows_all_tests_passed():
    ex = _execution(success=True, passed=5, total=5)
    result = _build(quality=Quality.OPTIMAL, execution=ex)
    assert "All tests passed" in result.content


def test_summary_correct_quality_all_passed():
    ex = _execution(success=True, passed=5, total=5)
    result = _build(quality=Quality.CORRECT, execution=ex)
    assert "All tests passed" in result.content


# ---------------------------------------------------------
# Partial pass (80%+ = CORRECT) — must NOT say "All tests passed"
# ---------------------------------------------------------


def test_summary_4_of_5_shows_partial_pass_count():
    ex = _execution(success=False, passed=4, total=5)
    result = _build(quality=Quality.CORRECT, execution=ex)
    assert "All tests passed" not in result.content
    assert "4/5" in result.content


def test_summary_4_of_5_shows_strong_solution():
    ex = _execution(success=False, passed=4, total=5)
    result = _build(quality=Quality.CORRECT, execution=ex)
    assert "Strong solution" in result.content


# ---------------------------------------------------------
# Incorrect / partial quality
# ---------------------------------------------------------


def test_summary_incorrect_quality():
    ex = _execution(success=False, passed=0, total=5)
    result = _build(quality=Quality.INCORRECT, execution=ex)
    assert "Incorrect Solution" in result.content
    assert "All tests passed" not in result.content


def test_summary_partial_quality():
    ex = _execution(success=False, passed=2, total=5)
    result = _build(quality=Quality.PARTIAL, execution=ex)
    assert "Partial Solution" in result.content
    assert "All tests passed" not in result.content


# ---------------------------------------------------------
# Written question — not affected by execution check
# ---------------------------------------------------------


def test_summary_written_correct_shows_great_answer():
    result = _build(quality=Quality.CORRECT, execution=None, is_coding=False)
    assert "Great answer" in result.content
