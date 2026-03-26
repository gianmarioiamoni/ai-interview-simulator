# tests/graph/nodes/test_execution_node.py

import pytest
from unittest.mock import Mock

from app.graph.nodes.execution_node import ExecutionNode
from tests.factories.interview_state_factory import build_interview_state
from domain.contracts.execution_result import ExecutionResult


def test_execution_node_success() -> None:
    # Arrange
    mock_engine = Mock()

    mock_result = Mock(spec=ExecutionResult)
    mock_result.success = True
    mock_result.question_id = "q1"

    mock_engine.execute.return_value = mock_result

    node = ExecutionNode(mock_engine)

    state = build_interview_state()

    # Act
    new_state = node(state)

    # Assert
    result = new_state.get_result_for_question("q1")

    assert result is not None
    assert result.execution is mock_result
    assert result.execution.success is True


def test_execution_node_failure() -> None:
    mock_engine = Mock()

    mock_result = Mock(spec=ExecutionResult)
    mock_result.success = False
    mock_result.question_id = "q1"

    mock_engine.execute.return_value = mock_result

    node = ExecutionNode(mock_engine)

    state = build_interview_state()

    new_state = node(state)

    result = new_state.get_result_for_question("q1")

    assert result is not None
    assert result.execution is mock_result
    assert result.execution.success is False


def test_execution_node_runtime_error() -> None:
    mock_engine = Mock()
    mock_engine.execute.side_effect = Exception("boom")

    node = ExecutionNode(mock_engine)

    state = build_interview_state()

    new_state = node(state)

    result = new_state.get_result_for_question("q1")

    # execution NON deve essere registrata
    assert result is None or result.execution is None


def test_execution_node_non_executable_question() -> None:
    mock_engine = Mock()

    node = ExecutionNode(mock_engine)

    state = build_interview_state(questions=[Mock(id="q1", type="hr")])

    new_state = node(state)

    result = new_state.get_result_for_question("q1")

    assert result is None
    mock_engine.execute.assert_not_called()


def test_execution_node_state_immutability() -> None:
    mock_engine = Mock()

    mock_result = Mock(spec=ExecutionResult)
    mock_result.success = True
    mock_result.question_id = "q1"

    mock_engine.execute.return_value = mock_result

    node = ExecutionNode(mock_engine)

    state = build_interview_state()

    new_state = node(state)

    # stato nuovo
    assert new_state is not state

    # stato originale NON modificato
    original_result = state.get_result_for_question("q1")
    assert original_result is None
