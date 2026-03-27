# tests/unit/graph/nodes/test_navigation_node.py

from app.graph.nodes.navigation_node import navigation_node


def build_state(**overrides):
    base = {
        "questions": [
            {"id": 1},
            {"id": 2},
            {"id": 3},
        ],
        "current_question_index": 0,
        "current_question": {"id": 1},
        "last_action": "next",
        "awaiting_user_input": False,
    }
    return {**base, **overrides}


def test_navigation_next_moves_forward():
    state = build_state(current_question_index=0)

    new_state = navigation_node(state)

    assert new_state["current_question_index"] == 1
    assert new_state["current_question"]["id"] == 2
    assert new_state["awaiting_user_input"] is True


def test_navigation_retry_keeps_same_question():
    state = build_state(last_action="retry", current_question_index=1)

    new_state = navigation_node(state)

    assert new_state["current_question_index"] == 1
    assert new_state["awaiting_user_input"] is True


def test_navigation_does_not_overflow():
    state = build_state(current_question_index=2)

    new_state = navigation_node(state)

    assert new_state["current_question_index"] == 2
    assert new_state["current_question"]["id"] == 3


def test_navigation_with_no_questions_is_safe():
    state = build_state(questions=[])

    new_state = navigation_node(state)

    assert new_state == state
