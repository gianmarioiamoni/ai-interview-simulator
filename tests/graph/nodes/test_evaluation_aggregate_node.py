# tests/graph/nodes/test_evaluation_aggregate_node.py
#
# Phase 7A: EvaluationAggregateNode writes scoring_snapshot, scoring_narrative,
# and interview_evaluation (bridge). Idempotency guard uses scoring_snapshot.

from unittest.mock import MagicMock, Mock, patch

import pytest

from app.graph.nodes.evaluation_aggregate_node import EvaluationAggregateNode
from tests.factories.interview_state_factory import build_interview_state
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.question.question_result import QuestionResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def _make_mock_snapshot():
    return MagicMock()


def _make_mock_narrative():
    return MagicMock()


def _make_service_mock(fail_evaluate: bool = False) -> Mock:
    """Return a service mock that satisfies both evaluate() and evaluate_scoring()."""
    service = Mock()
    if fail_evaluate:
        service.evaluate.side_effect = RuntimeError("LLM unavailable")
        service.evaluate_scoring.side_effect = RuntimeError("LLM unavailable")
    else:
        service.evaluate.return_value = MagicMock()
        service.evaluate_scoring.return_value = (_make_mock_snapshot(), _make_mock_narrative())
    return service


# ---------------------------------------------------------------------------
# Guard: empty results
# ---------------------------------------------------------------------------


def test_a2_no_results_returns_state_without_crash():
    """A2: empty results_by_question must not raise; state returned unchanged."""
    service = _make_service_mock()
    node = EvaluationAggregateNode(service=service)

    state = build_interview_state()
    state = state.model_copy(update={"is_completed": True})

    result_state = node(state)

    assert result_state is not None
    assert result_state.scoring_snapshot is None
    assert result_state.interview_evaluation is None
    service.evaluate.assert_not_called()
    service.evaluate_scoring.assert_not_called()


# ---------------------------------------------------------------------------
# Guard: service exception
# ---------------------------------------------------------------------------


def test_a2_service_exception_returns_state_without_crash():
    """A2: evaluation service failure must not propagate; state returned without evaluation."""
    service = _make_service_mock(fail_evaluate=True)
    node = EvaluationAggregateNode(service=service)

    state = build_interview_state()
    state = _make_state_with_result(state)

    result_state = node(state)

    assert result_state is not None
    assert result_state.scoring_snapshot is None
    assert result_state.interview_evaluation is None


# ---------------------------------------------------------------------------
# Happy path — writes all three artifacts
# ---------------------------------------------------------------------------


def test_a2_success_path_writes_all_three_artifacts():
    """Phase 7A: node writes scoring_snapshot, scoring_narrative, and interview_evaluation."""
    mock_eval = MagicMock()
    mock_snapshot = _make_mock_snapshot()
    mock_narrative = _make_mock_narrative()

    service = Mock()
    service.evaluate.return_value = mock_eval
    service.evaluate_scoring.return_value = (mock_snapshot, mock_narrative)

    node = EvaluationAggregateNode(service=service)

    state = build_interview_state()
    state = _make_state_with_result(state)

    result_state = node(state)

    assert result_state.interview_evaluation is mock_eval
    assert result_state.scoring_snapshot is mock_snapshot
    assert result_state.scoring_narrative is mock_narrative


def test_a2_success_path_sets_interview_evaluation():
    """Bridge compat: interview_evaluation is still set after Phase 7A."""
    service = _make_service_mock()
    node = EvaluationAggregateNode(service=service)

    state = build_interview_state()
    state = _make_state_with_result(state)

    result_state = node(state)

    assert result_state.interview_evaluation is not None


# ---------------------------------------------------------------------------
# Idempotency — guard uses scoring_snapshot (Phase 7A)
# ---------------------------------------------------------------------------


def test_idempotency_guard_uses_scoring_snapshot():
    """Phase 7A: node skips computation when scoring_snapshot is already set."""
    service = _make_service_mock()
    node = EvaluationAggregateNode(service=service)

    state = build_interview_state()
    state = _make_state_with_result(state)
    existing_snapshot = _make_mock_snapshot()
    state = state.model_copy(update={"scoring_snapshot": existing_snapshot})

    result_state = node(state)

    # Must not recompute
    service.evaluate.assert_not_called()
    service.evaluate_scoring.assert_not_called()
    assert result_state.scoring_snapshot is existing_snapshot


def test_idempotency_does_not_trigger_on_interview_evaluation_only():
    """Phase 7A: interview_evaluation alone does not satisfy idempotency guard."""
    service = _make_service_mock()
    node = EvaluationAggregateNode(service=service)

    state = build_interview_state()
    state = _make_state_with_result(state)
    # Set interview_evaluation but NOT scoring_snapshot
    state = state.model_copy(update={"interview_evaluation": MagicMock()})

    result_state = node(state)

    # Node must have re-run (scoring_snapshot was None)
    service.evaluate.assert_called_once()
    service.evaluate_scoring.assert_called_once()
