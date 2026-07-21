# tests/performance/test_slo_p_replay.py
# EPIC-V13-09 C4 — SLO-P: replay reconstruction < 1s; no DB store; no cache.

from __future__ import annotations

import inspect

from domain.contracts.replay.replay_session import ReplaySession
from tests.performance import slo_p
from tests.performance.slo_p import (
    SLO_P_TARGET_MS,
    measure_replay_reconstruction_ms,
    run_replay_reconstruction,
)
from tests.ui.replay.fixtures.session_history_20q import (
    QUESTION_COUNT_20,
    make_session_history_20q,
)


def test_replay_reconstruction_under_1s() -> None:
    """AR-04 / SLO-P: replay_node reconstruction wall-clock < 1s on ≥20q fixture."""
    session, elapsed_ms, history = measure_replay_reconstruction_ms()

    assert elapsed_ms >= 0.0
    assert elapsed_ms < SLO_P_TARGET_MS
    assert isinstance(session, ReplaySession)
    assert session.is_successful is True
    assert session.question_count == history.question_count == QUESTION_COUNT_20


def test_uses_materialized_session_loader_not_durable_db() -> None:
    """RPL-02/03 / MEAS-06: injected in-memory loader; no durable DB I/O."""
    source = inspect.getsource(slo_p)
    assert "sqlalchemy" not in source
    assert "sqlite" not in source
    assert "repository" not in source.lower()
    assert "materialized_session_loader" in source
    assert "make_session_history_20q" in source
    assert "SessionLoader" in source


def test_no_replay_session_cache_and_no_llm() -> None:
    """RPL-04/05: no ReplaySession cache; measurement introduces no LLM."""
    source = inspect.getsource(slo_p)
    import_block = "\n".join(
        line
        for line in source.splitlines()
        if line.startswith("from ") or line.startswith("import ")
    )
    assert "cache" not in import_block.lower()
    assert "lru_cache" not in source
    assert "llm" not in import_block.lower()
    assert "FakeLLM" not in source
    assert "DeterministicStubLLM" not in source


def test_repeated_reconstruction_is_independent() -> None:
    """RPL-04: each measurement rebuilds; no shared cached ReplaySession."""
    history = make_session_history_20q()
    first = run_replay_reconstruction(history)
    second = run_replay_reconstruction(history)
    assert first is not second
    assert first.session_id == second.session_id
    assert first.question_count == second.question_count == QUESTION_COUNT_20
