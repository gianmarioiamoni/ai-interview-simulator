# tests/unit/graph/nodes/test_report_node.py

from unittest.mock import Mock, patch

from app.graph.nodes.report_node import report_node


def build_state():
    return {
        "evaluations_list": [Mock()],
        "questions": [Mock()],
        "interview_type": "TECHNICAL",
        "role_type": "BACKEND_ENGINEER",
    }


@patch("app.graph.nodes.report_node.InterviewEvaluationService")
def test_report_node_builds_report(mock_service_cls):

    mock_service = Mock()
    mock_service_cls.return_value = mock_service

    mock_eval = Mock()
    mock_eval.overall_score = 80
    mock_eval.hiring_probability = 75
    mock_eval.percentile_rank = 85
    mock_eval.confidence.final = 0.9
    mock_eval.performance_dimensions = []
    mock_eval.improvement_suggestions = []
    mock_eval.executive_summary = "Good candidate"

    mock_service.evaluate.return_value = mock_eval

    state = build_state()

    new_state = report_node(state)

    assert "report_output" in new_state
    assert new_state["report_output"]["overall_score"] == 80
    assert new_state["interview_evaluation"] == mock_eval
