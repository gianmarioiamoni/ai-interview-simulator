from app.graph.nodes.decision_node import DecisionNode
from tests.factories.interview_state_factory import build_state_with_execution


def test_retry_when_failed_first_attempt():

    node = DecisionNode()

    state = build_state_with_execution(
        passed_tests=0,
        total_tests=5,
    )

    new_state = node(state)

    assert new_state.awaiting_user_input is True


def test_no_retry_after_max_attempts():

    node = DecisionNode(max_attempts=2)

    state = build_state_with_execution(
        passed_tests=0,
        total_tests=5,
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


def test_pass_moves_forward():

    node = DecisionNode()

    state = build_state_with_execution(
        passed_tests=5,
        total_tests=5,
    )

    new_state = node(state)

    assert new_state.awaiting_user_input is False
