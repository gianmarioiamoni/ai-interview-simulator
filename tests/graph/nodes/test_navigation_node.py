# tests/graph/nodes/test_navigation_node.py

from app.graph.nodes.navigation_node import navigation_node
from tests.factories.interview_state_factory import build_interview_state
from domain.contracts.action_type import ActionType


def test_navigation_next_moves_forward():

    state = build_interview_state()

    state = state.model_copy(
        update={
            "current_question_index": 0,
            "last_action": "next",
        }
    )

    new_state = navigation_node(state)

    assert new_state.current_question_index == 1
    assert new_state.last_action == ActionType.NEXT


def test_navigation_retry_keeps_same_question():

    state = build_interview_state()

    state = state.model_copy(
        update={
            "current_question_index": 1,
            "last_action": ActionType.RETRY,
        }
    )

    new_state = navigation_node(state)

    assert new_state.current_question_index == 1
    assert new_state.awaiting_user_input is True
    assert new_state.last_action == ActionType.RETRY


def test_navigation_does_not_overflow():

    state = build_interview_state()

    last_index = len(state.questions) - 1

    state = state.model_copy(
        update={
            "current_question_index": last_index,
            "last_action": ActionType.NEXT,
        }
    )

    new_state = navigation_node(state)

    assert new_state.current_question_index == last_index


def test_navigation_with_no_questions_is_safe():

    state = build_interview_state()

    state = state.model_copy(update={"questions": []})

    new_state = navigation_node(state)

    assert new_state == state
