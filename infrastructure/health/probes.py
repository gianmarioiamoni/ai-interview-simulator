# infrastructure/health/probes.py
#
# EPIC-08 P4/C9 — side-effect-free readiness probes (HLT-01–HLT-05; rejects AR-09).
# No LangGraph, no session/DB mutation, no interview/knowledge LLM cycles.

from __future__ import annotations

import sqlite3
import sys
import time
from collections.abc import Callable
from pathlib import Path

from infrastructure.config.settings import Settings
from infrastructure.health.types import ProbeResult

LLMConnectivityCheck = Callable[[Settings], None]


def probe_llm(
    settings: Settings,
    *,
    connectivity_check: LLMConnectivityCheck | None = None,
) -> ProbeResult:
    """LLM connectivity only — no chat/completions or interview prompts."""
    name = "llm"
    if not settings.health_llm_probe_enabled:
        return ProbeResult(name=name, status="skipped", detail="probe disabled")

    started = time.perf_counter()
    check = connectivity_check or _default_llm_connectivity_check
    try:
        check(settings)
        return ProbeResult(
            name=name,
            status="success",
            detail="llm api reachable",
            duration_ms=_elapsed_ms(started),
        )
    except Exception as exc:
        return ProbeResult(
            name=name,
            status="failure",
            detail=str(exc) or type(exc).__name__,
            error_type=type(exc).__name__,
            duration_ms=_elapsed_ms(started),
        )


def probe_database(settings: Settings) -> ProbeResult:
    """Read-only SQLite connectivity — never creates paths or mutates data."""
    name = "database"
    if not settings.health_db_probe_enabled:
        return ProbeResult(name=name, status="skipped", detail="probe disabled")

    started = time.perf_counter()
    db_path = Path(settings.sqlite_db_path)
    try:
        if not db_path.is_file():
            raise FileNotFoundError(f"sqlite database not found: {db_path}")
        uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=_timeout_seconds(settings))
        try:
            connection.execute("SELECT 1")
        finally:
            connection.close()
        return ProbeResult(
            name=name,
            status="success",
            detail="sqlite readable",
            duration_ms=_elapsed_ms(started),
        )
    except Exception as exc:
        return ProbeResult(
            name=name,
            status="failure",
            detail=str(exc) or type(exc).__name__,
            error_type=type(exc).__name__,
            duration_ms=_elapsed_ms(started),
        )


def probe_sandbox(settings: Settings) -> ProbeResult:
    """
    Execution sandbox readiness without running candidate/interview code.

    Verifies Python runtime presence and in-memory SQLite sandbox capability.
    """
    name = "sandbox"
    if not settings.health_sandbox_probe_enabled:
        return ProbeResult(name=name, status="skipped", detail="probe disabled")

    started = time.perf_counter()
    try:
        executable = Path(sys.executable)
        if not executable.is_file():
            raise RuntimeError(f"python executable unavailable: {executable}")

        connection = sqlite3.connect(":memory:", timeout=_timeout_seconds(settings))
        try:
            connection.execute("SELECT 1")
        finally:
            connection.close()

        return ProbeResult(
            name=name,
            status="success",
            detail="python runtime and in-memory sql sandbox available",
            duration_ms=_elapsed_ms(started),
        )
    except Exception as exc:
        return ProbeResult(
            name=name,
            status="failure",
            detail=str(exc) or type(exc).__name__,
            error_type=type(exc).__name__,
            duration_ms=_elapsed_ms(started),
        )


def _default_llm_connectivity_check(settings: Settings) -> None:
    """
    OpenAI models.list is connectivity-only (no chat, no business prompts).

    Uses Settings timeout; never invokes interview/knowledge generation.
    """
    from openai import OpenAI

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")

    client = OpenAI(
        api_key=settings.openai_api_key,
        timeout=_timeout_seconds(settings),
    )
    # Force a models.list round-trip without chat completions.
    # OpenAI SDK Models.list does not accept limit= (openai>=2.x).
    next(iter(client.models.list()), None)


def _timeout_seconds(settings: Settings) -> float:
    return max(settings.health_probe_timeout_ms, 1) / 1000.0


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)
