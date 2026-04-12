# tests/graph/nodes/test_decision_node.py

from app.graph.nodes.decision_node import DecisionNode
from tests.factories.interview_state_factory import build_state_with_execution
from domain.contracts.shared.action_type import ActionType


def test_retry_when_failed_first_attempt():

    node = DecisionNode()

    state = build_state_with_execution(
        passed_tests=0,
        total_tests=5,
        quality="incorrect",  # 🔥 REQUIRED
    )

    new_state = node(state)

    assert new_state.awaiting_user_input is True
    assert new_state.last_action == ActionType.RETRY


def test_no_retry_after_max_attempts():

    node = DecisionNode(max_attempts=2)

    state = build_state_with_execution(
        passed_tests=0,
        total_tests=5,
        quality="incorrect",
    )

    # simulate attempts
    state = state.model_copy(
        update={
            "answers": [
                state.answers[0],
                state.answers[0],
            ]
        }
    )

    new_state = node(state)

    assert new_state.awaiting_user_input is False
    assert new_state.last_action == ActionType.NEXT


def test_pass_moves_forward():

    node = DecisionNode()

    state = build_state_with_execution(
        passed_tests=5,
        total_tests=5,
        quality="correct",
    )

    new_state = node(state)

    assert new_state.awaiting_user_input is False
    assert new_state.last_action == ActionType.NEXT


def test_partial_triggers_retry():

    node = DecisionNode()

    state = build_state_with_execution(
        passed_tests=2,
        total_tests=5,
        quality="partial",
    )

    new_state = node(state)

    assert new_state.awaiting_user_input is True
    assert new_state.last_action == ActionType.RETRY
