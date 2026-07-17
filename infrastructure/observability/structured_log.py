# infrastructure/observability/structured_log.py
#
# EPIC-08 P2/C4 — sole emission path for Freeze §6.1 structured operational events.
# Infrastructure contract only (IB-03). Not a domain frozen model.

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Mapping

# Frozen schema field names (EPIC-08 Architecture Freeze §6.1). Stable for EPIC-09.
STRUCTURED_LOG_SCHEMA_FIELDS: tuple[str, ...] = (
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

_REQUIRED_ALWAYS: frozenset[str] = frozenset(
    {
        "timestamp",
        "level",
        "component",
        "event",
        "status",
    }
)

_LOGGER = logging.getLogger("infrastructure.observability.structured_log")

_LEVEL_TO_METHOD: Mapping[str, str] = {
    "DEBUG": "debug",
    "INFO": "info",
    "WARNING": "warning",
    "ERROR": "error",
    "CRITICAL": "critical",
}


def build_structured_log_payload(
    *,
    event: str,
    component: str,
    status: str,
    level: str = "INFO",
    session_id: str | None = None,
    execution_id: str | None = None,
    graph_node: str | None = None,
    duration_ms: float | int | None = None,
    model: str | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
    error_type: str | None = None,
    timestamp: str | None = None,
) -> dict[str, object]:
    """Build a Freeze §6.1 payload. Optional None fields are omitted (null/omit rule)."""
    resolved_timestamp = timestamp or datetime.now(timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    resolved_level = level.upper()

    payload: dict[str, object] = {
        "timestamp": resolved_timestamp,
        "level": resolved_level,
        "component": component,
        "event": event,
        "status": status,
    }

    optional: Mapping[str, object | None] = {
        "session_id": session_id,
        "execution_id": execution_id,
        "graph_node": graph_node,
        "duration_ms": duration_ms,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "error_type": error_type,
    }
    for key, value in optional.items():
        if value is not None:
            payload[key] = value

    _assert_required_fields(payload)
    return payload


def emit_structured_log(
    *,
    event: str,
    component: str,
    status: str,
    level: str = "INFO",
    session_id: str | None = None,
    execution_id: str | None = None,
    graph_node: str | None = None,
    duration_ms: float | int | None = None,
    model: str | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
    error_type: str | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, object]:
    """
    Emit one structured operational event via the sole schema emission path (OBS-01).

    OBS-03 / ARC-01 P-06: never alters caller control flow. Logger failures are
    absorbed at the emission boundary only; this helper does not catch or hide
    caller/application exceptions (callers must raise as usual).
    """
    payload = build_structured_log_payload(
        event=event,
        component=component,
        status=status,
        level=level,
        session_id=session_id,
        execution_id=execution_id,
        graph_node=graph_node,
        duration_ms=duration_ms,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        error_type=error_type,
    )
    _safe_emit(payload, logger=logger or _LOGGER)
    return payload


def _assert_required_fields(payload: Mapping[str, object]) -> None:
    missing = sorted(_REQUIRED_ALWAYS - frozenset(payload.keys()))
    if missing:
        raise ValueError(f"structured log payload missing required fields: {missing}")


def _safe_emit(payload: Mapping[str, object], *, logger: logging.Logger) -> None:
    method_name = _LEVEL_TO_METHOD.get(str(payload["level"]), "info")
    log_method = getattr(logger, method_name, logger.info)
    try:
        log_method(json.dumps(payload, separators=(",", ":"), default=str))
    except Exception:
        # Emission isolation only — must not raise into caller (OBS-03).
        return


def required_always_fields() -> frozenset[str]:
    return _REQUIRED_ALWAYS
