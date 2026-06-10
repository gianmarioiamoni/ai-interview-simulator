# infrastructure/llm/metrics/interview_metrics_collector.py

from contextvars import ContextVar

from infrastructure.llm.contracts.llm_call_metric import LLMCallMetric

_metrics_var: ContextVar[list[LLMCallMetric] | None] = ContextVar(
    "interview_llm_metrics",
    default=None,
)


class InterviewMetricsCollector:

    def start_session(self) -> None:
        _metrics_var.set([])

    def record(self, metric: LLMCallMetric) -> None:
        metrics = _metrics_var.get()
        if metrics is None:
            metrics = []
            _metrics_var.set(metrics)
        metrics.append(metric)

    def get_metrics(self) -> list[LLMCallMetric]:
        current = _metrics_var.get()
        if current is None:
            return []
        return list(current)

    def clear(self) -> None:
        _metrics_var.set([])
