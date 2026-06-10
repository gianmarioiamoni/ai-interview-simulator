# tests/integration/test_graph_snapshot.py

from unittest.mock import Mock

from app.graph.interview_graph import build_interview_graph


def test_interview_graph_compiles():

    llm = Mock()
    hint_service = Mock()

    compiled = build_interview_graph(llm=llm, hint_service=hint_service)

    assert compiled is not None


def test_interview_graph_contains_core_nodes():

    llm = Mock()
    hint_service = Mock()

    compiled = build_interview_graph(llm=llm, hint_service=hint_service)

    node_names = set(compiled.get_graph().nodes.keys())

    expected = {
        "router",
        "navigation",
        "execution",
        "evaluation",
        "feedback",
        "hint",
        "decision",
        "written",
        "completion",
        "report",
    }

    assert expected.issubset(node_names)
