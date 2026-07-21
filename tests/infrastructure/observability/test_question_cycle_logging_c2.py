# tests/infrastructure/observability/test_question_cycle_logging_c2.py
#
# EPIC-V13-09 C2 — optional cycle emit: existing schema only; no control-flow swallow.

from __future__ import annotations

import json
import logging
from typing import Any
from unittest.mock import patch

import pytest

from infrastructure.observability.question_cycle_logging import (
    QUESTION_CYCLE_COMPONENT,
    QUESTION_CYCLE_EVENT,
    emit_question_cycle_structured_log,
)
from infrastructure.observability.structured_log import (
    STRUCTURED_LOG_SCHEMA_FIELDS,
    emit_structured_log,
)


class _RaisingLogger(logging.Logger):
    def __init__(self) -> None:
        super().__init__("raising-question-cycle-log")

    def info(self, msg: object, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("logger boom")

    def error(self, msg: object, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("logger boom")


class TestQuestionCycleEmitSchema:
    def test_emit_uses_existing_freeze_schema_fields_only(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        logger = logging.getLogger("test.question_cycle.schema")
        with caplog.at_level(logging.INFO, logger=logger.name):
            payload = emit_question_cycle_structured_log(
                duration_ms=42.5,
                session_id="sess-1",
                execution_id="exec-1",
                logger=logger,
            )

        assert frozenset(payload.keys()) <= frozenset(STRUCTURED_LOG_SCHEMA_FIELDS)
        assert payload["event"] == QUESTION_CYCLE_EVENT
        assert payload["component"] == QUESTION_CYCLE_COMPONENT
        assert payload["duration_ms"] == 42.5
        assert payload["session_id"] == "sess-1"
        assert payload["execution_id"] == "exec-1"
        assert payload["status"] == "success"
        assert "graph_node" not in payload

        logged = json.loads(caplog.records[0].getMessage())
        assert frozenset(logged.keys()) <= frozenset(STRUCTURED_LOG_SCHEMA_FIELDS)
        assert logged["event"] == "question_cycle.complete"

    def test_optional_fields_omitted_when_absent(self) -> None:
        payload = emit_question_cycle_structured_log(duration_ms=1)
        assert "session_id" not in payload
        assert "execution_id" not in payload
        assert "error_type" not in payload
        assert payload["duration_ms"] == 1

    def test_routes_through_sole_emit_structured_log_path(self) -> None:
        with patch(
            "infrastructure.observability.question_cycle_logging.emit_structured_log",
            wraps=emit_structured_log,
        ) as mocked:
            emit_question_cycle_structured_log(
                duration_ms=10,
                session_id="s",
                execution_id="e",
            )
        mocked.assert_called_once()
        kwargs = mocked.call_args.kwargs
        assert kwargs["event"] == QUESTION_CYCLE_EVENT
        assert kwargs["component"] == QUESTION_CYCLE_COMPONENT
        assert kwargs["duration_ms"] == 10
        assert kwargs["session_id"] == "s"
        assert kwargs["execution_id"] == "e"


class TestQuestionCycleEmitControlFlow:
    def test_emission_failure_does_not_raise_into_caller(self) -> None:
        payload = emit_question_cycle_structured_log(
            duration_ms=3,
            logger=_RaisingLogger(),
        )
        assert payload["event"] == QUESTION_CYCLE_EVENT
        assert payload["status"] == "success"

    def test_helper_does_not_swallow_caller_exceptions(self) -> None:
        def _caller_that_fails() -> None:
            emit_question_cycle_structured_log(
                duration_ms=1,
                logger=_RaisingLogger(),
            )
            raise ValueError("application failure")

        with pytest.raises(ValueError, match="application failure"):
            _caller_that_fails()

    def test_failure_status_uses_error_level_by_default(self) -> None:
        payload = emit_question_cycle_structured_log(
            duration_ms=9,
            status="failure",
            error_type="TimeoutError",
            logger=_RaisingLogger(),
        )
        assert payload["status"] == "failure"
        assert payload["level"] == "ERROR"
        assert payload["error_type"] == "TimeoutError"
