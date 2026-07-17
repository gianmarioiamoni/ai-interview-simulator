# tests/infrastructure/observability/test_structured_log.py
#
# EPIC-08 P2/C4 — Freeze §6.1 helper: required fields, null/omit, OBS-03 isolation.

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

import pytest

from infrastructure.observability.structured_log import (
    STRUCTURED_LOG_SCHEMA_FIELDS,
    build_structured_log_payload,
    emit_structured_log,
    required_always_fields,
)


class _RaisingLogger(logging.Logger):
    def __init__(self) -> None:
        super().__init__("raising-structured-log")

    def info(self, msg: object, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("logger boom")

    def debug(self, msg: object, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("logger boom")

    def warning(self, msg: object, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("logger boom")

    def error(self, msg: object, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("logger boom")

    def critical(self, msg: object, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("logger boom")


class TestSchemaContract:
    def test_frozen_schema_field_names(self) -> None:
        assert STRUCTURED_LOG_SCHEMA_FIELDS == (
            "timestamp",
            "level",
            "session_id",
            "execution_id",
            "component",
            "graph_node",
            "event",
            "duration_ms",
            "model",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "status",
            "error_type",
        )

    def test_required_always_subset_of_schema(self) -> None:
        assert required_always_fields() <= frozenset(STRUCTURED_LOG_SCHEMA_FIELDS)


class TestBuildPayload:
    def test_required_fields_always_present(self) -> None:
        payload = build_structured_log_payload(
            event="node.complete",
            component="langgraph",
            status="success",
        )
        for field in required_always_fields():
            assert field in payload
            assert payload[field] is not None

    def test_null_optional_fields_are_omitted(self) -> None:
        payload = build_structured_log_payload(
            event="node.complete",
            component="langgraph",
            status="success",
            session_id=None,
            execution_id=None,
            graph_node=None,
            duration_ms=None,
            model=None,
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            error_type=None,
        )
        optional = (
            "session_id",
            "execution_id",
            "graph_node",
            "duration_ms",
            "model",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "error_type",
        )
        for field in optional:
            assert field not in payload

    def test_provided_optional_fields_are_present(self) -> None:
        payload = build_structured_log_payload(
            event="llm.call",
            component="llm",
            status="failure",
            level="ERROR",
            session_id="sess-1",
            execution_id="exec-1",
            graph_node="reasoner_node",
            duration_ms=12.5,
            model="gpt-4o-mini",
            prompt_tokens=10,
            completion_tokens=4,
            total_tokens=14,
            error_type="TimeoutError",
        )
        assert payload["session_id"] == "sess-1"
        assert payload["execution_id"] == "exec-1"
        assert payload["graph_node"] == "reasoner_node"
        assert payload["duration_ms"] == 12.5
        assert payload["model"] == "gpt-4o-mini"
        assert payload["prompt_tokens"] == 10
        assert payload["completion_tokens"] == 4
        assert payload["total_tokens"] == 14
        assert payload["error_type"] == "TimeoutError"
        assert payload["level"] == "ERROR"

    def test_timestamp_is_iso8601_utc(self) -> None:
        payload = build_structured_log_payload(
            event="tick",
            component="ops",
            status="success",
            timestamp="2026-07-18T00:00:00Z",
        )
        assert payload["timestamp"] == "2026-07-18T00:00:00Z"
        generated = build_structured_log_payload(
            event="tick",
            component="ops",
            status="success",
        )
        ts = str(generated["timestamp"])
        assert ts.endswith("Z")
        datetime.fromisoformat(ts.replace("Z", "+00:00"))

    def test_payload_keys_are_only_schema_fields(self) -> None:
        payload = build_structured_log_payload(
            event="node.complete",
            component="langgraph",
            status="success",
            graph_node="feedback_node",
            duration_ms=3,
        )
        assert frozenset(payload.keys()) <= frozenset(STRUCTURED_LOG_SCHEMA_FIELDS)


class TestEmitStructuredLog:
    def test_emit_returns_payload_and_logs_json(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        logger = logging.getLogger("test.structured_log.emit")
        with caplog.at_level(logging.INFO, logger=logger.name):
            payload = emit_structured_log(
                event="node.complete",
                component="langgraph",
                status="success",
                session_id="s1",
                graph_node="question_node",
                duration_ms=8,
                logger=logger,
            )
        assert payload["event"] == "node.complete"
        assert len(caplog.records) == 1
        logged = json.loads(caplog.records[0].getMessage())
        assert logged["session_id"] == "s1"
        assert logged["graph_node"] == "question_node"
        assert logged["duration_ms"] == 8
        assert logged["status"] == "success"

    def test_emission_does_not_raise_into_caller_control_flow(self) -> None:
        payload = emit_structured_log(
            event="node.complete",
            component="langgraph",
            status="success",
            logger=_RaisingLogger(),
        )
        assert payload["status"] == "success"

    def test_helper_does_not_swallow_caller_exceptions(self) -> None:
        """OBS-03: helper must not wrap/hide application failures."""

        def _caller_that_fails() -> None:
            emit_structured_log(
                event="before_failure",
                component="langgraph",
                status="success",
                logger=_RaisingLogger(),
            )
            raise ValueError("application failure")

        with pytest.raises(ValueError, match="application failure"):
            _caller_that_fails()
