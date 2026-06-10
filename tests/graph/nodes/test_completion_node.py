# tests/graph/nodes/test_completion_node.py

from app.graph.nodes.completion_node import completion_node
from tests.factories.interview_state_factory import build_interview_state


def test_completion_not_triggered_if_not_last():

    state = build_interview_state()

    state = state.model_copy(
        update={
            "current_question_index": 0,
        }
    )

    new_state = completion_node(state)

    assert new_state.is_completed is False


def test_completion_not_triggered_while_awaiting_user_input():

    state = build_interview_state()

    state = state.model_copy(
        update={
            "current_question_index": len(state.questions) - 1,
            "awaiting_user_input": True,
        }
    )

    new_state = completion_node(state)

    assert new_state.is_completed is False


def test_completion_triggers_on_last_question():

    state = build_interview_state()

    state = state.model_copy(
        update={
            "current_question_index": len(state.questions) - 1,
            "awaiting_user_input": False,
            "is_completed": False,
        }
    )

    new_state = completion_node(state)

    assert new_state.is_completed is True
