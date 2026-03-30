# tests/graph/nodes/test_completion_node.py

from app.graph.nodes.completion_node import completion_node
from tests.factories.interview_state_factory import build_interview_state


def test_completion_not_triggered_if_not_last():

    state = build_interview_state()

    state = state.model_copy(
        update={
            "current_question_index": 0,
            "last_action": "next",
        }
    )

    new_state = completion_node(state)

    assert new_state.is_completed is False


def test_completion_not_triggered_on_retry():

    state = build_interview_state()

    state = state.model_copy(update={"last_action": "retry"})

    new_state = completion_node(state)

    assert new_state.is_completed is False


def test_completion_triggers_on_last_question():

    state = build_interview_state()

    state = state.model_copy(
        update={
            "current_question_index": len(state.questions) - 1,
            "last_action": "next",
            "is_completed": False,
        }
    )

    new_state = completion_node(state)

    assert new_state.is_completed is True
    assert new_state.last_action is None
