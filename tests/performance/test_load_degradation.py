# tests/performance/test_load_degradation.py
# EPIC-V13-09 C8 — early vs late degradation gate (LOAD-03).

from __future__ import annotations

import pytest

from tests.performance.load_stub_sessions import (
    DEGRADATION_RATIO_MAX,
    EARLY_WINDOW_END,
    EARLY_WINDOW_START,
    LATE_WINDOW_END,
    LATE_WINDOW_START,
    LOAD_SESSION_COUNT,
    SLO_Q_P99_TARGET_MS,
    SLO_R_ABS_TARGET_MS,
    SessionLoadResult,
    StubLoadRunResult,
    analyze_degradation,
    assert_absolute_load_slos,
    assert_degradation_gate,
    run_stub_load,
)
from tests.performance.stub_llm import DeterministicStubLLM


def _synthetic_session(
    index: int,
    *,
    slo_q_ms: float,
    slo_r_ms: float,
) -> SessionLoadResult:
    return SessionLoadResult(
        session_index=index,
        slo_q_samples_ms=(slo_q_ms,) * 5,
        slo_r_ms=slo_r_ms,
        hard_failure=None,
    )


def _synthetic_load(
    *,
    early_q: float,
    early_r: float,
    late_q: float,
    late_r: float,
) -> StubLoadRunResult:
    sessions: list[SessionLoadResult] = []
    for index in range(1, LOAD_SESSION_COUNT + 1):
        if EARLY_WINDOW_START <= index <= EARLY_WINDOW_END:
            sessions.append(
                _synthetic_session(index, slo_q_ms=early_q, slo_r_ms=early_r)
            )
        elif LATE_WINDOW_START <= index <= LATE_WINDOW_END:
            sessions.append(
                _synthetic_session(index, slo_q_ms=late_q, slo_r_ms=late_r)
            )
        else:
            sessions.append(
                _synthetic_session(index, slo_q_ms=early_q, slo_r_ms=early_r)
            )
    return StubLoadRunResult(sessions=tuple(sessions))


def test_analyze_degradation_windows_and_ratio() -> None:
    """LOAD-03 wiring: sessions 1–10 vs 41–50; ratio = late/early."""
    result = _synthetic_load(early_q=100.0, early_r=50.0, late_q=120.0, late_r=60.0)
    analysis = analyze_degradation(result)

    assert analysis.early.start == EARLY_WINDOW_START
    assert analysis.early.end == EARLY_WINDOW_END
    assert analysis.late.start == LATE_WINDOW_START
    assert analysis.late.end == LATE_WINDOW_END
    assert analysis.early.session_count == 10
    assert analysis.late.session_count == 10
    assert analysis.slo_q_ratio == pytest.approx(1.2)
    assert analysis.slo_r_ratio == pytest.approx(1.2)
    assert analysis.slo_q_ratio <= DEGRADATION_RATIO_MAX
    assert_degradation_gate(result)


def test_degradation_gate_rejects_ratio_above_limit() -> None:
    result = _synthetic_load(early_q=100.0, early_r=50.0, late_q=130.0, late_r=50.0)
    with pytest.raises(AssertionError, match="SLO-Q late/early ratio"):
        assert_degradation_gate(result)


def test_degradation_gate_rejects_late_absolute_breach() -> None:
    result = _synthetic_load(
        early_q=100.0,
        early_r=50.0,
        late_q=SLO_Q_P99_TARGET_MS + 1.0,
        late_r=50.0,
    )
    with pytest.raises(AssertionError, match="late-window SLO-Q"):
        assert_degradation_gate(result)


def test_degradation_gate_rejects_late_slo_r_breach() -> None:
    result = _synthetic_load(
        early_q=100.0,
        early_r=50.0,
        late_q=100.0,
        late_r=SLO_R_ABS_TARGET_MS + 1.0,
    )
    with pytest.raises(AssertionError, match="late-window SLO-R"):
        assert_degradation_gate(result)


def test_analyze_degradation_requires_fifty_sessions() -> None:
    result = run_stub_load(session_count=2)
    with pytest.raises(ValueError, match="requires >= 50"):
        analyze_degradation(result)


@pytest.mark.slow
def test_fifty_session_stub_load_meets_degradation_gate() -> None:
    """LOAD-03: full stub load — absolute hold + late/early ≤ 1.25."""
    stub = DeterministicStubLLM()
    result = run_stub_load(session_count=LOAD_SESSION_COUNT, llm=stub)

    assert_absolute_load_slos(result)
    analysis = assert_degradation_gate(result)

    assert analysis.slo_q_ratio <= DEGRADATION_RATIO_MAX
    assert analysis.slo_r_ratio <= DEGRADATION_RATIO_MAX
    assert analysis.late.slo_q_p99_ms < SLO_Q_P99_TARGET_MS
    assert analysis.late.slo_r_max_ms < SLO_R_ABS_TARGET_MS
    assert result.to_dict()["degradation"]["slo_q_ratio"] == analysis.slo_q_ratio
