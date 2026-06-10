import pytest

from app.graph.nodes.evaluation_node import EvaluationNode
from tests.factories.interview_state_factory import build_interview_state
from domain.contracts.execution.execution_result import (
    ExecutionResult,
    ExecutionStatus,
    ExecutionType,
)
from tests.factories.interview_state_factory import build_state_with_execution


def test_evaluation_node_creates_evaluation():

    # Arrange
    node = EvaluationNode()

    state = build_interview_state()

    execution = ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        status=ExecutionStatus.SUCCESS,
        success=True,
        output="",
        error=None,
        passed_tests=2,
        total_tests=2,
        execution_time_ms=10,
        test_results=[],
    )

    state = state.model_copy(deep=True)
    state.register_execution(execution)

    # Act
    new_state = node(state)

    # Assert
    result = new_state.get_result_for_question("q1")

    assert result is not None
    assert result.evaluation is not None
    assert result.evaluation.score == 100


# tests/unit/graph/nodes/test_evaluation_node.py

from app.graph.nodes.evaluation_node import EvaluationNode
from tests.factories.interview_state_factory import build_state_with_execution


def test_evaluation_score_computation():

    node = EvaluationNode()

    state = build_state_with_execution(
        passed_tests=3,
        total_tests=5,
    )

    new_state = node(state)

    result = new_state.get_result_for_question("q1")

    assert result.evaluation.score == 60
    assert result.evaluation.passed is False
