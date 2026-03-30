# tests/graph/nodes/test_report_node.py

from unittest.mock import Mock

from app.graph.nodes.report_node import report_node
from tests.factories.interview_state_factory import build_interview_state

from domain.contracts.question_result import QuestionResult
from domain.contracts.question_evaluation import QuestionEvaluation


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

    # ---------------------------------------------------------
    # Build a valid evaluation in results_by_question
    # ---------------------------------------------------------

    question = state.current_question

    evaluation = QuestionEvaluation(
        question_id=question.id,
        score=80,
        max_score=100,
        passed=True,
        feedback="good",
        strengths=[],
        weaknesses=[],
    )

    result = QuestionResult(
        question_id=question.id,
        evaluation=evaluation,
    )

    state = state.model_copy(update={"results_by_question": {question.id: result}})

    # ---------------------------------------------------------
    # Execute node
    # ---------------------------------------------------------

    new_state = report_node(state, mock_service)

    # ---------------------------------------------------------
    # Assertions
    # ---------------------------------------------------------

    assert new_state.report_output is not None
    assert new_state.report_output["overall_score"] == 80

    assert hasattr(new_state, "interview_evaluation")
    assert new_state.interview_evaluation is not None

    mock_service.evaluate.assert_called_once()
