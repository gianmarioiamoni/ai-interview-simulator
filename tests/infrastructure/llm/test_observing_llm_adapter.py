# tests/infrastructure/llm/test_observing_llm_adapter.py

import json
from typing import Type, TypeVar
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from pydantic import BaseModel

from infrastructure.llm.metrics.interview_metrics_collector import (
    InterviewMetricsCollector,
)
from infrastructure.llm.observability.observing_llm_adapter import ObservingLLMAdapter

T = TypeVar("T", bound=BaseModel)


class _StubResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _StubLLMPort:
    def __init__(self, raw_llm: MagicMock) -> None:
        self._llm = raw_llm

    def invoke(self, prompt: str, system_prompt: str | None = None) -> _StubResponse:
        messages = [{"role": "user", "content": prompt}]
        raw = self._llm.invoke(messages)
        return _StubResponse(content=getattr(raw, "content", ""))

    def invoke_json(self, prompt: str, schema: Type[T]) -> T:
        for attempt in range(2):
            raw = self._llm.invoke([{"role": "user", "content": prompt}])
            content = getattr(raw, "content", "")
            try:
                return schema.model_validate(json.loads(content))
            except Exception:
                if attempt == 1:
                    raise ValueError("Failed to parse LLM JSON output") from None
        raise RuntimeError("unexpected")


class _DecisionSchema(BaseModel):
    drivers: list[str]
    blockers: list[str]


def _aimessage(content: str, **usage: int) -> AIMessage:
    return AIMessage(
        content=content,
        usage_metadata={
            "input_tokens": usage.get("input_tokens", 10),
            "output_tokens": usage.get("output_tokens", 5),
            "total_tokens": usage.get("total_tokens", 15),
        },
        response_metadata={
            "model_name": "gpt-4o-mini",
            "finish_reason": "stop",
        },
    )


def test_invoke_success_records_metric() -> None:
    collector = InterviewMetricsCollector()
    collector.start_session()

    raw_llm = MagicMock()
    raw_llm.model_name = "gpt-4o-mini"
    raw_llm.invoke.return_value = _aimessage("hello")

    adapter = ObservingLLMAdapter(_StubLLMPort(raw_llm), collector)
    response = adapter.invoke("hello")

    assert response.content == "hello"

    metrics = collector.get_metrics()
    assert len(metrics) == 1
    assert metrics[0].operation == "invoke"
    assert metrics[0].success is True
    assert metrics[0].attempt == 1
    assert metrics[0].input_tokens == 10
    assert metrics[0].output_tokens == 5
    assert metrics[0].total_tokens == 15
    assert metrics[0].model_name == "gpt-4o-mini"
    assert metrics[0].latency_ms >= 0


def test_invoke_failure_records_metric() -> None:
    collector = InterviewMetricsCollector()
    collector.start_session()

    raw_llm = MagicMock()
    raw_llm.model_name = "gpt-4o-mini"
    raw_llm.invoke.side_effect = RuntimeError("api down")

    adapter = ObservingLLMAdapter(_StubLLMPort(raw_llm), collector)

    with pytest.raises(RuntimeError, match="api down"):
        adapter.invoke("hello")

    metrics = collector.get_metrics()
    assert len(metrics) == 1
    assert metrics[0].operation == "invoke"
    assert metrics[0].success is False
    assert metrics[0].input_tokens is None
    assert metrics[0].total_tokens is None


def test_invoke_json_success_records_metric() -> None:
    collector = InterviewMetricsCollector()
    collector.start_session()

    payload = json.dumps({"drivers": ["a"], "blockers": ["b"]})
    raw_llm = MagicMock()
    raw_llm.model_name = "gpt-4o-mini"
    raw_llm.invoke.return_value = _aimessage(payload)

    adapter = ObservingLLMAdapter(_StubLLMPort(raw_llm), collector)
    parsed = adapter.invoke_json("prompt", _DecisionSchema)

    assert parsed.drivers == ["a"]

    metrics = collector.get_metrics()
    assert len(metrics) == 1
    assert metrics[0].operation == "invoke_json"
    assert metrics[0].success is True
    assert metrics[0].attempt == 1


def test_invoke_json_retry_records_each_attempt() -> None:
    collector = InterviewMetricsCollector()
    collector.start_session()

    payload = json.dumps({"drivers": ["a"], "blockers": ["b"]})
    raw_llm = MagicMock()
    raw_llm.model_name = "gpt-4o-mini"
    raw_llm.invoke.side_effect = [
        _aimessage("not-json"),
        _aimessage(payload),
    ]

    adapter = ObservingLLMAdapter(_StubLLMPort(raw_llm), collector)
    parsed = adapter.invoke_json("prompt", _DecisionSchema)

    assert parsed.blockers == ["b"]

    metrics = collector.get_metrics()
    assert len(metrics) == 2
    assert metrics[0].operation == "invoke_json"
    assert metrics[0].attempt == 1
    assert metrics[0].success is True
    assert metrics[1].operation == "invoke_json"
    assert metrics[1].attempt == 2
    assert metrics[1].success is True
