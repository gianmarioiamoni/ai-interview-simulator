# tests/graph/nodes/test_evaluation_node_sql_coaching.py

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
from domain.contracts.question.question import QuestionType
from domain.contracts.question.question_result import QuestionResult
from tests.factories.interview_state_factory import build_interview_state, build_question


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sql_test(
    *,
    tid: int = 0,
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


def _build_db_state(execution: ExecutionResult):
    question = build_question(qid="q1", qtype=QuestionType.DATABASE)
    state = build_interview_state(questions=[question, build_question(qid="q2", qtype=QuestionType.DATABASE)])
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
    state = _build_db_state(execution)
    new_state = EvaluationNode()(state)
    result = new_state.get_result_for_question("q1")
    assert result is not None and result.evaluation is not None
    return result.evaluation


# ---------------------------------------------------------------------------
# 1. Perfect SQL solution
# ---------------------------------------------------------------------------


def test_perfect_sql_solution():
    execution = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.DATABASE,
        status=ExecutionStatus.SUCCESS,
        success=True,
        output="",
        error=None,
        passed_tests=3,
        total_tests=3,
        execution_time_ms=10,
        test_results=[
            _make_sql_test(tid=i, status=TestStatus.PASSED,
                           expected=[("a",)], actual=[("a",)])
            for i in range(3)
        ],
    )
    ev = _run(execution)

    assert "Correct query logic demonstrated across all tested scenarios" in ev.strengths
    assert "Query executed successfully without runtime errors" in ev.strengths
    assert ev.weaknesses == []


# ---------------------------------------------------------------------------
# 2. Successful execution (no errors, but tested separately from perfect)
# ---------------------------------------------------------------------------


def test_successful_execution_no_errors():
    execution = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.DATABASE,
        status=ExecutionStatus.SUCCESS,
        success=True,
        output="",
        error=None,
        passed_tests=2,
        total_tests=2,
        execution_time_ms=5,
        test_results=[
            _make_sql_test(tid=i, status=TestStatus.PASSED,
                           expected=[("x",)], actual=[("x",)])
            for i in range(2)
        ],
    )
    ev = _run(execution)

    assert "Query executed successfully without runtime errors" in ev.strengths


# ---------------------------------------------------------------------------
# 3. Syntax error
# ---------------------------------------------------------------------------


def test_syntax_error_weakness():
    execution = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.DATABASE,
        status=ExecutionStatus.RUNTIME_ERROR,
        success=False,
        output="",
        error='near "SELEC": syntax error',
        passed_tests=0,
        total_tests=1,
        execution_time_ms=2,
        test_results=[
            _make_sql_test(
                tid=0,
                status=TestStatus.ERROR,
                error='near "SELEC": syntax error',
            )
        ],
    )
    ev = _run(execution)

    assert "SQL syntax issues detected" in ev.weaknesses
    assert "Correct query logic demonstrated across all tested scenarios" not in ev.strengths


# ---------------------------------------------------------------------------
# 4. Schema error (no such table / column)
# ---------------------------------------------------------------------------


def test_schema_error_weakness():
    execution = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.DATABASE,
        status=ExecutionStatus.RUNTIME_ERROR,
        success=False,
        output="",
        error="no such table: orders",
        passed_tests=0,
        total_tests=1,
        execution_time_ms=2,
        test_results=[
            _make_sql_test(
                tid=0,
                status=TestStatus.ERROR,
                error="no such table: orders",
            )
        ],
    )
    ev = _run(execution)

    assert "Schema understanding issues detected" in ev.weaknesses


# ---------------------------------------------------------------------------
# 5. Logic failure → LogicIssueAnalyzer message
# ---------------------------------------------------------------------------


def test_logic_failure_produces_analyzer_weakness():
    execution = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.DATABASE,
        status=ExecutionStatus.FAILED_TESTS,
        success=False,
        output="",
        error="Test execution failed",
        passed_tests=0,
        total_tests=1,
        execution_time_ms=5,
        test_results=[
            _make_sql_test(
                tid=0,
                status=TestStatus.FAILED,
                expected=[("alice",), ("bob",)],
                actual=[],
            )
        ],
    )
    ev = _run(execution)

    assert any(
        "missing" in w.lower() or "incorrect" in w.lower() or "rows" in w.lower()
        for w in ev.weaknesses
    ), f"Expected logic weakness, got: {ev.weaknesses}"


# ---------------------------------------------------------------------------
# 6. Empty-result issue → EdgeCaseDetector
# ---------------------------------------------------------------------------


def test_empty_result_weakness():
    execution = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.DATABASE,
        status=ExecutionStatus.FAILED_TESTS,
        success=False,
        output="",
        error="Test execution failed",
        passed_tests=1,
        total_tests=2,
        execution_time_ms=8,
        test_results=[
            _make_sql_test(
                tid=0,
                status=TestStatus.PASSED,
                expected=[("a",)],
                actual=[("a",)],
            ),
            _make_sql_test(
                tid=1,
                status=TestStatus.FAILED,
                expected=[],
                actual=[("x",)],
            ),
        ],
    )
    ev = _run(execution)

    assert "Query does not correctly handle empty-result scenarios" in ev.weaknesses
