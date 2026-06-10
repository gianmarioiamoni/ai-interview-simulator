# tests/infrastructure/llm/test_interview_metrics_collector.py

import asyncio

from infrastructure.llm.contracts.llm_call_metric import LLMCallMetric
from infrastructure.llm.metrics.interview_metrics_collector import (
    InterviewMetricsCollector,
)
from datetime import datetime, timezone


def _metric(operation: str = "invoke") -> LLMCallMetric:
    return LLMCallMetric(
        operation=operation,
        model_name="gpt-4o-mini",
        latency_ms=12.5,
        attempt=1,
        success=True,
        input_tokens=10,
        output_tokens=5,
        total_tokens=15,
        timestamp=datetime.now(timezone.utc),
    )


def test_record_and_get_metrics() -> None:
    collector = InterviewMetricsCollector()
    collector.start_session()

    collector.record(_metric("invoke"))
    collector.record(_metric("invoke_json"))

    metrics = collector.get_metrics()

    assert len(metrics) == 2
    assert metrics[0].operation == "invoke"
    assert metrics[1].operation == "invoke_json"


def test_clear() -> None:
    collector = InterviewMetricsCollector()
    collector.start_session()
    collector.record(_metric())

    collector.clear()

    assert collector.get_metrics() == []


def test_contextvar_isolation() -> None:
    collector = InterviewMetricsCollector()

    async def worker(label: str) -> str:
        collector.start_session()
        collector.record(_metric(label))
        await asyncio.sleep(0)
        return collector.get_metrics()[0].operation

    async def main() -> list[str]:
        return list(await asyncio.gather(worker("worker-a"), worker("worker-b")))

    results = asyncio.run(main())

    assert set(results) == {"worker-a", "worker-b"}
