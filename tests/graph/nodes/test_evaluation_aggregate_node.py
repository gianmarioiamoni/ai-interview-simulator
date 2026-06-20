# tests/graph/nodes/test_evaluation_aggregate_node.py

from unittest.mock import Mock, MagicMock

from app.graph.nodes.evaluation_aggregate_node import EvaluationAggregateNode
from tests.factories.interview_state_factory import build_interview_state
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.question.question_evaluation import QuestionEvaluation


def _make_state_with_result(state, score: float = 80.0):
    """Attach a minimal QuestionResult with an evaluation so the node can run."""
    question = state.current_question
    evaluation = QuestionEvaluation(
        question_id=question.id,
        score=score,
        max_score=100.0,
        passed=score >= 60,
        feedback="ok",
    )
    result = QuestionResult(
        question_id=question.id,
        question=question,
        evaluation=evaluation,
    )
    new_results = dict(state.results_by_question)
    new_results[question.id] = result
    return state.model_copy(update={"results_by_question": new_results, "is_completed": True})


def test_a2_no_results_returns_state_without_crash():
    """A2: empty results_by_question must not raise; state returned unchanged."""
    mock_service = Mock()
    node = EvaluationAggregateNode(service=mock_service)

    state = build_interview_state()
    state = state.model_copy(update={"is_completed": True})

    result_state = node(state)

    assert result_state is not None
    assert result_state.interview_evaluation is None
    mock_service.evaluate.assert_not_called()


def test_a2_service_exception_returns_state_without_crash():
    """A2: evaluation service failure must not propagate; state returned without evaluation."""
    mock_service = Mock()
    mock_service.evaluate.side_effect = RuntimeError("LLM unavailable")

    node = EvaluationAggregateNode(service=mock_service)

    state = build_interview_state()
    state = _make_state_with_result(state)

    result_state = node(state)

    assert result_state is not None
    assert result_state.interview_evaluation is None


def test_a2_success_path_sets_interview_evaluation():
    """A2: happy path still writes interview_evaluation."""
    mock_eval = MagicMock()
    mock_service = Mock()
    mock_service.evaluate.return_value = mock_eval

    node = EvaluationAggregateNode(service=mock_service)

    state = build_interview_state()
    state = _make_state_with_result(state)

    result_state = node(state)

    assert result_state.interview_evaluation is mock_eval
