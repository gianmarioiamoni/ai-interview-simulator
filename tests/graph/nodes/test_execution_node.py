# tests/graph/nodes/test_execution_node.py

from unittest.mock import Mock

from app.graph.nodes.execution_node import ExecutionNode
from tests.factories.interview_state_factory import build_interview_state
from tests.factories.question_factory import build_question

from domain.contracts.execution.execution_result import ExecutionResult
from domain.contracts.question.question import QuestionType


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
    # Arrange
    mock_engine = Mock()

    mock_result = Mock(spec=ExecutionResult)
    mock_result.success = False
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
    assert result.execution.success is False


def test_execution_node_runtime_error_creates_error_result() -> None:
    """A1: execution exception must produce an INTERNAL_ERROR QuestionResult."""
    from domain.contracts.execution.execution_result import ExecutionStatus

    mock_engine = Mock()
    mock_engine.execute.side_effect = Exception("boom")

    node = ExecutionNode(mock_engine)
    state = build_interview_state()

    new_state = node(state)

    result = new_state.get_result_for_question("q1")
    assert result is not None, "QuestionResult must exist even after execution failure"
    assert result.execution is not None, "execution must be populated on failure"
    assert result.execution.success is False
    assert result.execution.status == ExecutionStatus.INTERNAL_ERROR
    assert "boom" in (result.execution.error or "")


def test_execution_node_non_executable_question() -> None:
    # Arrange
    mock_engine = Mock()

    node = ExecutionNode(mock_engine)

    state = build_interview_state(
        questions=[build_question(qtype=QuestionType.WRITTEN)]
    )

    # Act
    new_state = node(state)

    # Assert
    result = new_state.get_result_for_question("q1")

    assert result is None
    mock_engine.execute.assert_not_called()


def test_execution_node_state_immutability() -> None:
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
    # nuovo stato
    assert new_state is not state

    # stato originale NON modificato
    original_result = state.get_result_for_question("q1")
    assert original_result is None
