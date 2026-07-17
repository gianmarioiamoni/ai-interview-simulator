# tests/infrastructure/llm/test_observing_llm_adapter_c7.py
#
# EPIC-08 P3/C7 — AR-07 fields on existing ObservingLLMAdapter / collector path.

from __future__ import annotations

import json
from typing import Type, TypeVar
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from pydantic import BaseModel

from infrastructure.llm.contracts.llm_call_metric import LLMCallMetric
from infrastructure.llm.metrics.interview_metrics_collector import (
    InterviewMetricsCollector,
)
from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext
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
        raw = self._llm.invoke([{"role": "user", "content": prompt}])
        content = getattr(raw, "content", "")
        return schema.model_validate(json.loads(content))


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


class TestAr07FieldsOnExistingPath:
    def test_success_records_tokens_latency_model_and_aliases(self) -> None:
        collector = InterviewMetricsCollector()
        collector.start_session()
        raw_llm = MagicMock()
        raw_llm.model_name = "gpt-4o-mini"
        raw_llm.invoke.return_value = _aimessage("ok")

        adapter = ObservingLLMAdapter(_StubLLMPort(raw_llm), collector)
        with LLMOperationContext.scope("written_evaluation"):
            adapter.invoke("hello")

        metric = collector.get_metrics()[0]
        assert metric.model_name == "gpt-4o-mini"
        assert metric.model == "gpt-4o-mini"
        assert metric.latency_ms >= 0
        assert metric.duration_ms == metric.latency_ms
        assert metric.input_tokens == 10
        assert metric.prompt_tokens == 10
        assert metric.output_tokens == 5
        assert metric.completion_tokens == 5
        assert metric.total_tokens == 15
        assert metric.status == "success"
        assert metric.error_type is None
        assert metric.operation == "written_evaluation"

        fields = metric.as_ar07_fields()
        assert fields["model"] == "gpt-4o-mini"
        assert fields["prompt_tokens"] == 10
        assert fields["completion_tokens"] == 5
        assert fields["total_tokens"] == 15
        assert fields["duration_ms"] == metric.latency_ms
        assert fields["status"] == "success"
        assert fields["error_type"] is None
        assert fields["operation"] == "written_evaluation"

    def test_failure_records_error_type_and_model_without_swallowing(self) -> None:
        collector = InterviewMetricsCollector()
        collector.start_session()
        raw_llm = MagicMock()
        raw_llm.model_name = "gpt-4o-mini"
        raw_llm.invoke.side_effect = RuntimeError("api down")

        adapter = ObservingLLMAdapter(_StubLLMPort(raw_llm), collector)
        with LLMOperationContext.scope("hint_generation"):
            with pytest.raises(RuntimeError, match="api down"):
                adapter.invoke("hello")

        metric = collector.get_metrics()[0]
        assert metric.success is False
        assert metric.status == "failure"
        assert metric.error_type == "RuntimeError"
        assert metric.model == "gpt-4o-mini"
        assert metric.duration_ms >= 0
        assert metric.as_ar07_fields()["error_type"] == "RuntimeError"

    def test_sole_collector_path_records_metric(self) -> None:
        collector = InterviewMetricsCollector()
        collector.start_session()
        raw_llm = MagicMock()
        raw_llm.model_name = "gpt-4o-mini"
        raw_llm.invoke.return_value = _aimessage("ok")

        adapter = ObservingLLMAdapter(_StubLLMPort(raw_llm), collector)
        adapter.invoke("hello")

        assert len(collector.get_metrics()) == 1
        assert isinstance(collector.get_metrics()[0], LLMCallMetric)
