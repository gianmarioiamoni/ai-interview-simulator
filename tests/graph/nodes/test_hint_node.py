# tests/unit/graph/nodes/test_hint_node.py

from unittest.mock import Mock

from app.graph.nodes.hint_node import HintNode
from domain.contracts.execution_result import ExecutionResult, ExecutionStatus, ExecutionType
from tests.factories.interview_state_factory import build_state_with_execution



def test_hint_level_progression_partial():

    node = HintNode(Mock())

    state = build_state_with_execution(
        passed_tests=2,
        total_tests=5,
        quality="partial",
    )

    new_state = node(state)

    result = new_state.get_result_for_question("q1")

    assert result.hint_level is not None
