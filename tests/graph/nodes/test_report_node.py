# tests/graph/nodes/test_report_node.py

from unittest.mock import Mock

from app.graph.nodes.report_node import report_node
from tests.factories.interview_state_factory import build_interview_state

from domain.contracts.question.question_result import QuestionResult
from domain.contracts.question.question_evaluation import QuestionEvaluation


def test_report_node_preserves_interview_evaluation():

    mock_service = Mock()

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

    interview_eval = Mock()

    state = state.model_copy(
        update={
            "results_by_question": {question.id: result},
            "interview_evaluation": interview_eval,
            "is_processing": True,
        }
    )

    # ---------------------------------------------------------
    # Execute node
    # ---------------------------------------------------------

    new_state = report_node(state, mock_service)

    # ---------------------------------------------------------
    # Assertions
    # ---------------------------------------------------------

    assert new_state.interview_evaluation is interview_eval
    assert new_state.is_processing is False


def test_report_node_without_evaluations_clears_interview_evaluation():

    mock_service = Mock()

    state = build_interview_state()

    state = state.model_copy(
        update={
            "results_by_question": {},
            "interview_evaluation": Mock(),
        }
    )

    new_state = report_node(state, mock_service)

    assert new_state.interview_evaluation is None
