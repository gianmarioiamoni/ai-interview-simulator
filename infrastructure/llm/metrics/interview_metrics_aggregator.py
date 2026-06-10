# infrastructure/llm/metrics/interview_metrics_aggregator.py

from collections import defaultdict

from domain.contracts.interview.interview_metrics import InterviewMetrics, OperationMetrics
from infrastructure.llm.contracts.llm_call_metric import LLMCallMetric


class InterviewMetricsAggregator:

    def aggregate(self, metrics: list[LLMCallMetric]) -> InterviewMetrics:
        if not metrics:
            return InterviewMetrics(
                total_calls=0,
                total_input_tokens=0,
                total_output_tokens=0,
                total_tokens=0,
                total_retries=0,
                avg_latency_ms=0.0,
                operations=[],
            )

        total_input = sum(m.input_tokens or 0 for m in metrics)
        total_output = sum(m.output_tokens or 0 for m in metrics)
        total_tokens = sum(m.total_tokens or 0 for m in metrics)
        total_retries = sum(1 for m in metrics if m.attempt > 1)
        avg_latency = sum(m.latency_ms for m in metrics) / len(metrics)

        grouped: dict[str, list[LLMCallMetric]] = defaultdict(list)
        for metric in metrics:
            grouped[metric.operation].append(metric)

        operations: list[OperationMetrics] = []
        for operation in sorted(grouped):
            items = grouped[operation]
            operations.append(
                OperationMetrics(
                    operation=operation,
                    calls=len(items),
                    input_tokens=sum(m.input_tokens or 0 for m in items),
                    output_tokens=sum(m.output_tokens or 0 for m in items),
                    total_tokens=sum(m.total_tokens or 0 for m in items),
                    avg_latency_ms=sum(m.latency_ms for m in items) / len(items),
                )
            )

        return InterviewMetrics(
            total_calls=len(metrics),
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_tokens=total_tokens,
            total_retries=total_retries,
            avg_latency_ms=avg_latency,
            operations=operations,
        )
