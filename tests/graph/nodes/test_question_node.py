# tests/graph/nodes/test_question_node.py

from unittest.mock import Mock

from app.graph.nodes.question_node import build_question_node
from tests.factories.interview_state_factory import build_interview_state
from domain.contracts.question import QuestionType


def test_question_node_no_question():

    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()
    state = state.model_copy(update={"current_question_index": -1})

    new_state = node(state)

    assert new_state == state


def test_question_node_prevents_double_processing():

    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()

    # simulate already processed
    state.chat_history.append("already processed")

    new_state = node(state)

    assert new_state.chat_history == state.chat_history


def test_question_node_humanizer_disabled():

    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()
    state = state.model_copy(update={"enable_humanizer": False})

    question = state.current_question

    new_state = node(state)

    assert question.prompt in new_state.chat_history


def test_question_node_non_written():

    llm = Mock()
    node = build_question_node(llm)

    state = build_interview_state()

    q = state.current_question.model_copy(update={"type": QuestionType.CODING})
    state = state.model_copy(update={"questions": [q]})

    new_state = node(state)

    assert q.prompt in new_state.chat_history


def test_question_node_humanized():

    llm = Mock()
    llm.invoke.return_value = Mock(content="humanized question")

    node = build_question_node(llm)

    state = build_interview_state()

    from domain.contracts.question import QuestionType

    q = state.current_question.model_copy(update={"type": QuestionType.WRITTEN})

    state = state.model_copy(
        update={
            "questions": [q],
            "chat_history": [],
            "current_question_index": 0,
            "enable_humanizer": True,
        }
    )

    new_state = node(state)

    assert "humanized question" in new_state.chat_history
    llm.invoke.assert_called_once()
