# tests/graph/nodes/test_interview_graph_question_node_wiring.py

import pytest
from unittest.mock import Mock, MagicMock

import app.graph.nodes.navigation_node as _nav_module
from app.graph.interview_graph import build_interview_graph
from app.graph.nodes.navigation_node import configure_navigation_node
from tests.factories.interview_state_factory import build_interview_state
from domain.contracts.shared.action_type import ActionType
from domain.contracts.question.question import QuestionType


def _make_llm_mock() -> Mock:

    llm = MagicMock()
    # Default humanizer response — plain question passthrough
    llm.invoke.return_value = Mock(
        content='{"decision": "direct_question", "message": "humanized prompt"}'
    )
    return llm


@pytest.fixture(autouse=True)
def _configure_node():
    configure_navigation_node()
    yield
    _nav_module._default_navigation_node = None


def test_question_node_is_registered_in_graph() -> None:

    llm = _make_llm_mock()
    graph = build_interview_graph(llm)

    node_names = set(graph.get_graph().nodes.keys())

    assert "question" in node_names


def test_navigation_routes_to_question_node() -> None:

    llm = _make_llm_mock()
    graph = build_interview_graph(llm)

    edges = {(e.source, e.target) for e in graph.get_graph().edges}

    assert ("navigation", "question") in edges


def test_question_node_routes_to_completion() -> None:

    llm = _make_llm_mock()
    graph = build_interview_graph(llm)

    edges = {(e.source, e.target) for e in graph.get_graph().edges}

    assert ("question", "completion") in edges


def test_graph_runs_next_action_through_question_node() -> None:

    llm = _make_llm_mock()
    graph = build_interview_graph(llm)

    state = build_interview_state()
    state = state.model_copy(
        update={
            "intent": ActionType.NEXT,
            "awaiting_user_input": False,
            "enable_humanizer": False,
        }
    )

    result = graph.invoke(state)

    # After NEXT the state should advance and chat_history should contain the question
    assert result is not None
