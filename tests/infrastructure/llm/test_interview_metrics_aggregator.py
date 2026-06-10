# tests/infrastructure/llm/test_interview_metrics_aggregator.py

from datetime import datetime, timezone

from infrastructure.llm.contracts.llm_call_metric import LLMCallMetric
from infrastructure.llm.metrics.interview_metrics_aggregator import (
    InterviewMetricsAggregator,
)


def _metric(
    *,
    operation: str = "written_evaluation",
    attempt: int = 1,
    latency_ms: float = 100.0,
    input_tokens: int | None = 10,
    output_tokens: int | None = 5,
    total_tokens: int | None = 15,
) -> LLMCallMetric:
    return LLMCallMetric(
        operation=operation,
        model_name="gpt-4o-mini",
        latency_ms=latency_ms,
        attempt=attempt,
        success=True,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        timestamp=datetime.now(timezone.utc),
    )


def test_aggregate_empty_metrics() -> None:
    result = InterviewMetricsAggregator().aggregate([])

    assert result.total_calls == 0
    assert result.total_tokens == 0
    assert result.total_retries == 0
    assert result.avg_latency_ms == 0.0
    assert result.operations == []


def test_aggregate_single_metric() -> None:
    result = InterviewMetricsAggregator().aggregate([_metric()])

    assert result.total_calls == 1
    assert result.total_input_tokens == 10
    assert result.total_output_tokens == 5
    assert result.total_tokens == 15
    assert result.total_retries == 0
    assert result.avg_latency_ms == 100.0
    assert len(result.operations) == 1
    assert result.operations[0].operation == "written_evaluation"


def test_aggregate_multiple_operations() -> None:
    metrics = [
        _metric(operation="question_generation", total_tokens=100, input_tokens=80, output_tokens=20),
        _metric(operation="written_evaluation", total_tokens=50, input_tokens=30, output_tokens=20),
        _metric(operation="narrative_generation", total_tokens=200, input_tokens=150, output_tokens=50),
    ]

    result = InterviewMetricsAggregator().aggregate(metrics)

    assert result.total_calls == 3
    assert result.total_tokens == 350
    assert len(result.operations) == 3
    assert [op.operation for op in result.operations] == [
        "narrative_generation",
        "question_generation",
        "written_evaluation",
    ]


def test_aggregate_retry_counting() -> None:
    metrics = [
        _metric(operation="narrative_generation", attempt=1),
        _metric(operation="narrative_generation", attempt=2),
    ]

    result = InterviewMetricsAggregator().aggregate(metrics)

    assert result.total_calls == 2
    assert result.total_retries == 1
    assert result.operations[0].calls == 2


def test_aggregate_latency_averaging() -> None:
    metrics = [
        _metric(latency_ms=100.0),
        _metric(latency_ms=300.0),
    ]

    result = InterviewMetricsAggregator().aggregate(metrics)

    assert result.avg_latency_ms == 200.0
    assert result.operations[0].avg_latency_ms == 200.0
