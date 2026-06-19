# tests/graph/nodes/test_evaluation_node_coaching.py

import pytest

from app.graph.nodes.evaluation_node import EvaluationNode
from domain.contracts.execution.execution_result import (
    ExecutionResult,
    ExecutionStatus,
    ExecutionType,
)
from domain.contracts.execution.test_execution_result import (
    TestExecutionResult,
    TestStatus,
    TestType,
)
from domain.contracts.question.question_result import QuestionResult
from tests.factories.interview_state_factory import build_interview_state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_test(
    *,
    tid: int = 1,
    status: TestStatus = TestStatus.PASSED,
    expected=None,
    actual=None,
    error: str | None = None,
) -> TestExecutionResult:
    return TestExecutionResult(
        id=tid,
        type=TestType.VISIBLE,
        status=status,
        expected=expected,
        actual=actual,
        error=error,
    )


def _build_state_with_execution(execution: ExecutionResult):
    state = build_interview_state()
    question = state.current_question
    new_results = dict(state.results_by_question)
    new_results[question.id] = QuestionResult(
        question_id=question.id,
        execution=execution,
        evaluation=None,
        ai_hint=None,
        hint_level=None,
    )
    return state.model_copy(update={"results_by_question": new_results})


def _run(execution: ExecutionResult):
    state = _build_state_with_execution(execution)
    new_state = EvaluationNode()(state)
    result = new_state.get_result_for_question("q1")
    assert result is not None and result.evaluation is not None
    return result.evaluation


# ---------------------------------------------------------------------------
# 1. Perfect solution
# ---------------------------------------------------------------------------


def test_perfect_solution_strengths():
    execution = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        status=ExecutionStatus.SUCCESS,
        success=True,
        output="",
        error=None,
        passed_tests=5,
        total_tests=5,
        execution_time_ms=20,
        test_results=[_make_test(tid=i, status=TestStatus.PASSED) for i in range(1, 6)],
    )
    evaluation = _run(execution)

    assert "All test cases passed" in evaluation.strengths
    assert "No runtime errors detected" in evaluation.strengths
    assert "Efficient execution time" in evaluation.strengths
    assert evaluation.weaknesses == []


# ---------------------------------------------------------------------------
# 2. Partial solution
# ---------------------------------------------------------------------------


def test_partial_solution_weaknesses():
    execution = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        status=ExecutionStatus.FAILED_TESTS,
        success=False,
        output="",
        error="Some tests failed",
        passed_tests=3,
        total_tests=5,
        execution_time_ms=50,
        test_results=[
            _make_test(tid=1, status=TestStatus.PASSED),
            _make_test(tid=2, status=TestStatus.PASSED),
            _make_test(tid=3, status=TestStatus.PASSED),
            _make_test(tid=4, status=TestStatus.FAILED, expected=4, actual=0),
            _make_test(tid=5, status=TestStatus.FAILED, expected=10, actual=5),
        ],
    )
    evaluation = _run(execution)

    assert "All test cases passed" not in evaluation.strengths
    assert any("Partial" in w or "passed" in w for w in evaluation.weaknesses)


# ---------------------------------------------------------------------------
# 3. Runtime error
# ---------------------------------------------------------------------------


def test_runtime_error_weakness():
    execution = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        status=ExecutionStatus.RUNTIME_ERROR,
        success=False,
        output="",
        error="NameError: name 'x' is not defined",
        passed_tests=0,
        total_tests=0,
        execution_time_ms=5,
        test_results=[],
    )
    evaluation = _run(execution)

    assert any("runtime" in w.lower() or "Runtime" in w for w in evaluation.weaknesses)
    assert "All test cases passed" not in evaluation.strengths


# ---------------------------------------------------------------------------
# 4. Edge-case failure
# ---------------------------------------------------------------------------


def test_edge_case_failure_weakness():
    execution = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        status=ExecutionStatus.FAILED_TESTS,
        success=False,
        output="",
        error="Some tests failed",
        passed_tests=4,
        total_tests=5,
        execution_time_ms=30,
        test_results=[
            _make_test(tid=1, status=TestStatus.PASSED),
            _make_test(tid=2, status=TestStatus.PASSED),
            _make_test(tid=3, status=TestStatus.PASSED),
            _make_test(tid=4, status=TestStatus.PASSED),
            _make_test(tid=5, status=TestStatus.FAILED, expected=[], actual=[1, 2]),
        ],
    )
    evaluation = _run(execution)

    assert any("edge" in w.lower() or "Edge" in w for w in evaluation.weaknesses)


# ---------------------------------------------------------------------------
# 5. Inefficient execution (slow but correct)
# ---------------------------------------------------------------------------


def test_slow_execution_no_efficiency_strength():
    execution = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        status=ExecutionStatus.SUCCESS,
        success=True,
        output="",
        error=None,
        passed_tests=5,
        total_tests=5,
        execution_time_ms=500,
        test_results=[_make_test(tid=i, status=TestStatus.PASSED) for i in range(1, 6)],
    )
    evaluation = _run(execution)

    assert "All test cases passed" in evaluation.strengths
    assert "Efficient execution time" not in evaluation.strengths
    assert evaluation.weaknesses == []
