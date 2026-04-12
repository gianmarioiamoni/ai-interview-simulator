# tests/unit/graph/nodes/test_hint_node.py

from unittest.mock import Mock

from app.graph.nodes.hint_node import HintNode
from domain.contracts.ai.hint_level import HintLevel
from tests.factories.interview_state_factory import build_state_with_execution


# ---------------------------------------------------------
# HELPER
# ---------------------------------------------------------


def run_hint_node(state, expected_level):

    mock_service = Mock()
    mock_service.generate_hint.return_value = "test hint"

    node = HintNode(mock_service)

    new_state = node(state)

    result = new_state.get_result_for_question("q1")

    if expected_level == HintLevel.NONE:
        # no hint generated
        assert result.hint_level is None
        assert result.ai_hint is None
        mock_service.generate_hint.assert_not_called()
    else:
        assert result.hint_level == expected_level
        assert result.ai_hint == "test hint"
        mock_service.generate_hint.assert_called_once()


# ---------------------------------------------------------
# TESTS
# ---------------------------------------------------------


def test_hint_correct_no_hint():

    state = build_state_with_execution(
        passed_tests=5,
        total_tests=5,
        quality="correct",
    )

    run_hint_node(state, HintLevel.NONE)


def test_hint_partial_first_attempt():

    state = build_state_with_execution(
        passed_tests=2,
        total_tests=5,
        quality="partial",
    )

    run_hint_node(state, HintLevel.BASIC)


def test_hint_partial_second_attempt():

    state = build_state_with_execution(
        passed_tests=2,
        total_tests=5,
        quality="partial",
    )

    # simulate second attempt
    state = state.model_copy(update={"answers": [state.answers[0], state.answers[0]]})

    run_hint_node(state, HintLevel.TARGETED)


def test_hint_partial_third_attempt():

    state = build_state_with_execution(
        passed_tests=2,
        total_tests=5,
        quality="partial",
    )

    # simulate third attempt
    state = state.model_copy(
        update={
            "answers": [
                state.answers[0],
                state.answers[0],
                state.answers[0],
            ]
        }
    )

    run_hint_node(state, HintLevel.SOLUTION)


def test_hint_incorrect_first_attempt():

    state = build_state_with_execution(
        passed_tests=0,
        total_tests=5,
        quality="incorrect",
    )

    run_hint_node(state, HintLevel.TARGETED)


def test_hint_incorrect_second_attempt():

    state = build_state_with_execution(
        passed_tests=0,
        total_tests=5,
        quality="incorrect",
    )

    state = state.model_copy(update={"answers": [state.answers[0], state.answers[0]]})

    run_hint_node(state, HintLevel.SOLUTION)
