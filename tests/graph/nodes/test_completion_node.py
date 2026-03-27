from app.graph.nodes.completion_node import completion_node


def build_state(**overrides):
    base = {
        "questions": [{"id": 1}, {"id": 2}],
        "current_question_index": 1,
        "last_action": "next",
        "is_completed": False,
    }
    return {**base, **overrides}


def test_completion_triggers_on_last_question():
    state = build_state()

    new_state = completion_node(state)

    assert new_state["is_completed"] is True


def test_completion_not_triggered_if_not_last():
    state = build_state(current_question_index=0)

    new_state = completion_node(state)

    assert new_state.get("is_completed") is False


def test_completion_not_triggered_on_retry():
    state = build_state(last_action="retry")

    new_state = completion_node(state)

    assert new_state.get("is_completed") is False
