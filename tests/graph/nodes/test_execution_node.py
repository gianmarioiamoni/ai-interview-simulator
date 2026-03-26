# tests/graph/nodes/test_execution_node.py

import pytest
from unittest.mock import Mock

from app.graph.nodes.execution_node import ExecutionNode
from domain.contracts.interview_state import InterviewState


def test_execution_node_success() -> None:
    # Arrange
    mock_engine = Mock()

    mock_result = Mock()
    mock_result.success = True

    mock_engine.execute.return_value = mock_result

    node = ExecutionNode(mock_engine)

    state = InterviewState(
        current_question=Mock(type="coding"),
        current_answer=Mock(),
    )

    # Act
    new_state = node(state)

    # Assert
    assert new_state.execution_success is True
    assert new_state.execution_result is mock_result
    assert new_state.execution_error is None


def test_execution_node_failure() -> None:
    mock_engine = Mock()

    mock_result = Mock()
    mock_result.success = False

    mock_engine.execute.return_value = mock_result

    node = ExecutionNode(mock_engine)

    state = InterviewState(
        current_question=Mock(type="coding"),
        current_answer=Mock(),
    )

    new_state = node(state)

    assert new_state.execution_success is False
    assert new_state.execution_result is mock_result
    assert new_state.execution_error is None


def test_execution_node_runtime_error() -> None:
    mock_engine = Mock()
    mock_engine.execute.side_effect = Exception("boom")

    node = ExecutionNode(mock_engine)

    state = InterviewState(
        current_question=Mock(type="coding"),
        current_answer=Mock(),
    )

    new_state = node(state)

    assert new_state.execution_success is False
    assert new_state.execution_result is None
    assert new_state.execution_error == "boom"


def test_execution_node_non_executable() -> None:
    mock_engine = Mock()

    node = ExecutionNode(mock_engine)

    state = InterviewState(
        current_question=Mock(type="hr"),
        current_answer=Mock(),
    )

    new_state = node(state)

    assert new_state.execution_success is True
    assert new_state.execution_result is None
    assert new_state.execution_error is None

    mock_engine.execute.assert_not_called()
