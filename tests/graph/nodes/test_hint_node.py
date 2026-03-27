# tests/graph/nodes/test_hint_node.py

from unittest.mock import Mock

from app.graph.nodes.hint_node import HintNode
from domain.contracts.hint_level import HintLevel
from tests.factories.interview_state_factory import build_state_with_execution


def test_hint_level_progression_partial():

    mock_service = Mock()
    mock_service.generate_hint.return_value = "test hint"

    node = HintNode(mock_service)

    state = build_state_with_execution(
        passed_tests=2,
        total_tests=5,
        quality="partial",
    )

    new_state = node(state)

    result = new_state.get_result_for_question("q1")

    assert result.hint_level == HintLevel.BASIC
    assert result.ai_hint == "test hint"

    mock_service.generate_hint.assert_called_once()
