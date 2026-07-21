# tests/performance/test_load_stub_sessions.py
# EPIC-V13-09 C7 — 50-session stub load: absolute SLO-Q/SLO-R + zero hard failures.

from __future__ import annotations

import pytest

from tests.performance.load_stub_sessions import (
    LOAD_SESSION_COUNT,
    SLO_Q_P99_TARGET_MS,
    SLO_R_ABS_TARGET_MS,
    WRITTEN_QUESTIONS_PER_SESSION,
    assert_absolute_load_slos,
    run_stub_load,
)
from tests.performance.stub_llm import DeterministicStubLLM


@pytest.mark.slow
def test_fifty_session_stub_load_meets_absolute_slos() -> None:
    """LOAD-01/02/04/05: 50×5 written sessions; SLO-Q P99 < 8s; SLO-R max < 3s."""
    stub = DeterministicStubLLM()
    result = run_stub_load(session_count=LOAD_SESSION_COUNT, llm=stub)

    assert result.session_count == LOAD_SESSION_COUNT
    assert len(result.sessions) == LOAD_SESSION_COUNT
    assert result.questions_per_session == WRITTEN_QUESTIONS_PER_SESSION
    assert all(s.session_index == i for i, s in enumerate(result.sessions, start=1))
    assert all(
        len(s.slo_q_samples_ms) == WRITTEN_QUESTIONS_PER_SESSION
        for s in result.sessions
        if s.succeeded
    )
    assert stub.invoke_call_count >= LOAD_SESSION_COUNT * WRITTEN_QUESTIONS_PER_SESSION

    assert_absolute_load_slos(result)
    assert result.hard_failure_count() == 0
    assert result.slo_q_p99_ms() < SLO_Q_P99_TARGET_MS
    assert result.slo_r_max_ms() < SLO_R_ABS_TARGET_MS


def test_load_runner_shape_and_stub_primary_smoke() -> None:
    """Small smoke: stub path, session shape, absolute helper (not full 50)."""
    stub = DeterministicStubLLM()
    result = run_stub_load(session_count=2, llm=stub)

    assert len(result.sessions) == 2
    assert result.hard_failure_count() == 0
    assert len(result.all_slo_q_ms()) == 2 * WRITTEN_QUESTIONS_PER_SESSION
    assert len(result.all_slo_r_ms()) == 2
    assert stub.invoke_call_count == 2 * WRITTEN_QUESTIONS_PER_SESSION
    assert_absolute_load_slos(result)

    payload = result.to_dict()
    assert payload["session_count"] == 2
    assert payload["hard_failure_count"] == 0
    assert payload["slo_q_p99_ms"] is not None
    assert payload["slo_r_max_ms"] is not None


def test_run_stub_load_rejects_invalid_session_count() -> None:
    with pytest.raises(ValueError, match="session_count"):
        run_stub_load(session_count=0)
