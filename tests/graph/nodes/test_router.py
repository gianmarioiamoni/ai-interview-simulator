# tests/unit/graph/nodes/test_router_node.py

from app.graph.interview_graph import route_by_question_type
from tests.factories.interview_state_factory import build_written_question_state


def test_router_written():

    state = build_written_question_state()

    route = route_by_question_type(state)

    assert route == "written"
