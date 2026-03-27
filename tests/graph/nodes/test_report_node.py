from unittest.mock import Mock

from app.graph.nodes.report_node import report_node
from tests.factories.interview_state_factory import build_interview_state


def test_report_node_builds_report():

    mock_service = Mock()

    mock_eval = Mock()
    mock_eval.overall_score = 80
    mock_eval.hiring_probability = 75
    mock_eval.percentile_rank = 85

    mock_eval.confidence = Mock()
    mock_eval.confidence.final = 0.9

    mock_eval.performance_dimensions = []
    mock_eval.improvement_suggestions = []
    mock_eval.executive_summary = "Good candidate"

    mock_service.evaluate.return_value = mock_eval

    state = build_interview_state()

    new_state = report_node(state, mock_service)

    assert new_state.report_output["overall_score"] == 80
    assert new_state.interview_evaluation == mock_eval
