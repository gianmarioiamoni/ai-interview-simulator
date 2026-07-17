# tests/infrastructure/llm/test_llm_structured_log_bridge_c8.py
#
# EPIC-08 P3/C8 — ObservingLLMAdapter → emit_structured_log bridge (OBS-04/05).

from __future__ import annotations

import ast
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Type, TypeVar
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage
from pydantic import BaseModel

from infrastructure.llm.contracts.llm_call_metric import LLMCallMetric
from infrastructure.llm.metrics.interview_metrics_collector import (
    InterviewMetricsCollector,
)
from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext
from infrastructure.llm.observability.llm_structured_log_bridge import (
    emit_llm_call_structured_log,
)
from infrastructure.llm.observability.observing_llm_adapter import ObservingLLMAdapter
from infrastructure.observability.structured_log import emit_structured_log

T = TypeVar("T", bound=BaseModel)

REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTER_PATH = (
    REPO_ROOT / "infrastructure" / "llm" / "observability" / "observing_llm_adapter.py"
)
BRIDGE_PATH = (
    REPO_ROOT
    / "infrastructure"
    / "llm"
    / "observability"
    / "llm_structured_log_bridge.py"
)


class _StubResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _StubLLMPort:
    def __init__(self, raw_llm: MagicMock) -> None:
        self._llm = raw_llm

    def invoke(self, prompt: str, system_prompt: str | None = None) -> _StubResponse:
        raw = self._llm.invoke([{"role": "user", "content": prompt}])
        return _StubResponse(content=getattr(raw, "content", ""))

    def invoke_json(self, prompt: str, schema: Type[T]) -> T:
        raw = self._llm.invoke([{"role": "user", "content": prompt}])
        return schema.model_validate(json.loads(getattr(raw, "content", "")))


def _aimessage(content: str) -> AIMessage:
    return AIMessage(
        content=content,
        usage_metadata={
            "input_tokens": 11,
            "output_tokens": 7,
            "total_tokens": 18,
        },
        response_metadata={"model_name": "gpt-4o-mini", "finish_reason": "stop"},
    )


def _metric(*, success: bool = True) -> LLMCallMetric:
    return LLMCallMetric(
        operation="written_evaluation",
        model_name="gpt-4o-mini",
        latency_ms=12.5,
        attempt=1,
        success=success,
        input_tokens=11,
        output_tokens=7,
        total_tokens=18,
        timestamp=datetime.now(timezone.utc),
        error_type=None if success else "RuntimeError",
    )


class TestBridgeEmission:
    def test_success_emits_model_tokens_duration_via_helper(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        logger = logging.getLogger("infrastructure.observability.structured_log")
        with caplog.at_level(logging.INFO, logger=logger.name):
            payload = emit_llm_call_structured_log(_metric(success=True))

        assert payload["event"] == "llm.call"
        assert payload["component"] == "llm"
        assert payload["status"] == "success"
        assert payload["model"] == "gpt-4o-mini"
        assert payload["prompt_tokens"] == 11
        assert payload["completion_tokens"] == 7
        assert payload["total_tokens"] == 18
        assert payload["duration_ms"] == 12.5
        assert "error_type" not in payload
        assert len(caplog.records) == 1
        logged = json.loads(caplog.records[0].getMessage())
        assert logged["model"] == "gpt-4o-mini"
        assert logged["duration_ms"] == 12.5

    def test_failure_emits_status_and_error_type(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        logger = logging.getLogger("infrastructure.observability.structured_log")
        with caplog.at_level(logging.ERROR, logger=logger.name):
            payload = emit_llm_call_structured_log(_metric(success=False))

        assert payload["status"] == "failure"
        assert payload["error_type"] == "RuntimeError"
        assert payload["model"] == "gpt-4o-mini"
        assert payload["duration_ms"] == 12.5

    def test_bridge_calls_sole_structured_helper(self) -> None:
        with patch(
            "infrastructure.llm.observability.llm_structured_log_bridge.emit_structured_log",
            wraps=emit_structured_log,
        ) as mocked:
            emit_llm_call_structured_log(_metric())
        mocked.assert_called_once()
        kwargs = mocked.call_args.kwargs
        assert kwargs["event"] == "llm.call"
        assert kwargs["model"] == "gpt-4o-mini"
        assert kwargs["prompt_tokens"] == 11
        assert kwargs["completion_tokens"] == 7
        assert kwargs["total_tokens"] == 18
        assert kwargs["duration_ms"] == 12.5


class TestAdapterUsesBridgeOnly:
    def test_adapter_records_metric_and_emits_via_bridge(self) -> None:
        collector = InterviewMetricsCollector()
        collector.start_session()
        raw_llm = MagicMock()
        raw_llm.model_name = "gpt-4o-mini"
        raw_llm.invoke.return_value = _aimessage("ok")

        adapter = ObservingLLMAdapter(_StubLLMPort(raw_llm), collector)
        with (
            LLMOperationContext.scope("narrative_generation"),
            patch(
                "infrastructure.llm.observability.observing_llm_adapter.emit_llm_call_structured_log"
            ) as bridge,
        ):
            adapter.invoke("hello")

        assert len(collector.get_metrics()) == 1
        bridge.assert_called_once()
        emitted = bridge.call_args.args[0]
        assert emitted.model == "gpt-4o-mini"
        assert emitted.prompt_tokens == 11
        assert emitted.duration_ms >= 0
        assert emitted.status == "success"

    def test_failure_still_propagates_after_bridge(self) -> None:
        collector = InterviewMetricsCollector()
        collector.start_session()
        raw_llm = MagicMock()
        raw_llm.model_name = "gpt-4o-mini"
        raw_llm.invoke.side_effect = RuntimeError("api down")

        adapter = ObservingLLMAdapter(_StubLLMPort(raw_llm), collector)
        with patch(
            "infrastructure.llm.observability.observing_llm_adapter.emit_llm_call_structured_log"
        ) as bridge:
            with pytest.raises(RuntimeError, match="api down"):
                adapter.invoke("hello")

        bridge.assert_called_once()
        assert bridge.call_args.args[0].status == "failure"
        assert bridge.call_args.args[0].error_type == "RuntimeError"


class TestSoleEmissionPathArchitecture:
    def test_adapter_does_not_call_emit_structured_log_directly(self) -> None:
        source = ADAPTER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    assert alias.name != "emit_structured_log"
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    assert func.id != "emit_structured_log"
                if isinstance(func, ast.Attribute):
                    assert func.attr != "emit_structured_log"

    def test_bridge_is_sole_llm_structured_emitter(self) -> None:
        source = BRIDGE_PATH.read_text(encoding="utf-8")
        assert "emit_structured_log" in source
        assert "emit_llm_call_structured_log" in source
