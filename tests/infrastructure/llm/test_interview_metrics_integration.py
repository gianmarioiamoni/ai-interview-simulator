# tests/infrastructure/llm/test_interview_metrics_integration.py

from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.graph.nodes.evaluation_aggregate_node import EvaluationAggregateNode
from domain.contracts.interview.interview_evaluation import InterviewEvaluation
from domain.contracts.interview.interview_metrics import InterviewMetrics, OperationMetrics
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.shared.action_type import ActionType
from domain.contracts.user.role import Role, RoleType
from infrastructure.llm.contracts.llm_call_metric import LLMCallMetric
from infrastructure.llm.metrics.interview_metrics_collector import (
    InterviewMetricsCollector,
)
from infrastructure.llm.metrics.interview_metrics_aggregator import (
    InterviewMetricsAggregator,
)
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.question.question_result import QuestionResult
from tests.factories.interview_state_factory import build_interview_state


def test_collector_aggregator_state_totals_match() -> None:
    collector = InterviewMetricsCollector()
    collector.start_session()

    collector.record(
        LLMCallMetric(
            operation="question_generation",
            model_name="gpt-4o-mini",
            latency_ms=1000.0,
            attempt=1,
            success=True,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            timestamp=datetime.now(timezone.utc),
        )
    )
    collector.record(
        LLMCallMetric(
            operation="written_evaluation",
            model_name="gpt-4o-mini",
            latency_ms=2000.0,
            attempt=1,
            success=True,
            input_tokens=200,
            output_tokens=100,
            total_tokens=300,
            timestamp=datetime.now(timezone.utc),
        )
    )

    aggregated = InterviewMetricsAggregator().aggregate(collector.get_metrics())

    assert aggregated.total_calls == 2
    assert aggregated.total_tokens == 450
    assert aggregated.total_input_tokens == 300
    assert aggregated.total_output_tokens == 150


def test_evaluation_aggregate_node_stores_interview_metrics(monkeypatch) -> None:
    collector = InterviewMetricsCollector()
    collector.start_session()
    collector.record(
        LLMCallMetric(
            operation="narrative_generation",
            model_name="gpt-4o-mini",
            latency_ms=500.0,
            attempt=1,
            success=True,
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
            timestamp=datetime.now(timezone.utc),
        )
    )

    monkeypatch.setattr(
        "app.runtime.interview_runtime.get_runtime_metrics_collector",
        lambda: collector,
    )

    mock_eval = MagicMock(spec=InterviewEvaluation)
    mock_eval.overall_score = 80.0
    mock_service = MagicMock()
    mock_service.evaluate_all.return_value = (mock_eval, MagicMock(), MagicMock())

    node = EvaluationAggregateNode(mock_service)
    state = build_interview_state()
    state = state.model_copy(
        update={
            "is_completed": True,
            "role": Role(type=RoleType.BACKEND_ENGINEER),
            "interview_type": InterviewType.TECHNICAL,
            "results_by_question": {
                "q1": QuestionResult(
                    question_id="q1",
                    evaluation=QuestionEvaluation(
                        question_id="q1",
                        score=80.0,
                        max_score=100.0,
                        feedback="Solid answer",
                        passed=True,
                    ),
                )
            },
        }
    )

    updated = node(state)

    assert updated.interview_metrics is not None
    assert updated.interview_metrics.total_calls == 1
    assert updated.interview_metrics.total_tokens == 15
    assert updated.interview_cost_metrics is not None
    assert updated.interview_cost_metrics.total_cost_usd > 0.0
    assert updated.interview_cost_metrics.cost_per_question_usd > 0.0
    assert updated.interview_evaluation is mock_eval
    assert updated.intent == ActionType.NONE
