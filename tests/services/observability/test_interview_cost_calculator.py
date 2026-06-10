# tests/services/observability/test_interview_cost_calculator.py

from domain.contracts.interview.interview_metrics import InterviewMetrics, OperationMetrics
from services.observability.interview_cost_calculator import InterviewCostCalculator


def _metrics(
    *,
    total_input: int = 0,
    total_output: int = 0,
    operations: list[OperationMetrics] | None = None,
) -> InterviewMetrics:
    return InterviewMetrics(
        total_calls=len(operations or []),
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_tokens=total_input + total_output,
        total_retries=0,
        avg_latency_ms=0.0,
        operations=operations or [],
    )


def test_operation_cost_calculation() -> None:
    metrics = _metrics(
        total_input=1_000_000,
        total_output=0,
        operations=[
            OperationMetrics(
                operation="written_evaluation",
                calls=1,
                input_tokens=1_000_000,
                output_tokens=0,
                total_tokens=1_000_000,
                avg_latency_ms=100.0,
            )
        ],
    )

    result = InterviewCostCalculator().calculate(metrics, question_count=1)

    assert result.operations[0].operation == "written_evaluation"
    assert result.operations[0].cost_usd == 0.15
    assert result.total_cost_usd == 0.15


def test_interview_aggregation_matches_total_tokens() -> None:
    metrics = _metrics(
        total_input=2_000_000,
        total_output=1_000_000,
        operations=[
            OperationMetrics(
                operation="question_generation",
                calls=1,
                input_tokens=1_000_000,
                output_tokens=500_000,
                total_tokens=1_500_000,
                avg_latency_ms=100.0,
            ),
            OperationMetrics(
                operation="narrative_generation",
                calls=1,
                input_tokens=1_000_000,
                output_tokens=500_000,
                total_tokens=1_500_000,
                avg_latency_ms=200.0,
            ),
        ],
    )

    result = InterviewCostCalculator().calculate(metrics, question_count=2)

    operation_total = sum(op.cost_usd for op in result.operations)
    assert result.total_cost_usd == operation_total
    assert result.total_cost_usd == 0.9
    assert result.cost_per_question_usd == 0.45


def test_zero_token_interview() -> None:
    result = InterviewCostCalculator().calculate(_metrics(), question_count=3)

    assert result.total_cost_usd == 0.0
    assert result.cost_per_question_usd == 0.0
    assert result.operations == []


def test_integration_metrics_to_cost_metrics() -> None:
    metrics = InterviewMetrics(
        total_calls=2,
        total_input_tokens=10_000,
        total_output_tokens=5_000,
        total_tokens=15_000,
        total_retries=0,
        avg_latency_ms=250.0,
        operations=[
            OperationMetrics(
                operation="hint_generation",
                calls=1,
                input_tokens=4_000,
                output_tokens=1_000,
                total_tokens=5_000,
                avg_latency_ms=200.0,
            ),
            OperationMetrics(
                operation="written_evaluation",
                calls=1,
                input_tokens=6_000,
                output_tokens=4_000,
                total_tokens=10_000,
                avg_latency_ms=300.0,
            ),
        ],
    )

    result = InterviewCostCalculator().calculate(metrics, question_count=1)

    assert len(result.operations) == 2
    assert result.total_cost_usd > 0.0
    assert result.cost_per_question_usd == result.total_cost_usd
