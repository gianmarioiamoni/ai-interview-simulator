# tests/performance/test_slo_q_written_cycle.py
# EPIC-V13-09 C1 — SLO-Q measurability: written invoke wall-clock + stub + P99 helper.

from __future__ import annotations

import pytest

from tests.performance.helpers import p99_ms, percentile_nearest_rank
from tests.performance.slo_q import measure_written_cycle_ms
from tests.performance.stub_llm import DeterministicStubLLM

# Wiring constant from Implementation Plan §3 (absolute gate enforced under load in C7).
_SLO_Q_P99_TARGET_MS = 8000.0


def test_written_cycle_wall_clock_is_measurable() -> None:
    """AR-01/AR-02: harness measures one written graph.invoke at invoke boundary."""
    result, elapsed_ms, stub = measure_written_cycle_ms()

    assert elapsed_ms >= 0.0
    assert stub.invoke_call_count >= 1
    evaluation = result.get_result_for_question("q1")
    assert evaluation is not None
    assert evaluation.evaluation is not None
    assert evaluation.evaluation.score == 95.0
    assert result.awaiting_user_input is True


def test_written_cycle_uses_deterministic_stub_path() -> None:
    """AR-16 / LOAD-05: primary path is deterministic stub LLM (no live network)."""
    stub = DeterministicStubLLM()
    result, elapsed_ms, used = measure_written_cycle_ms(llm=stub)

    assert used is stub
    assert stub.invoke_call_count == 1
    assert elapsed_ms < _SLO_Q_P99_TARGET_MS
    assert result.get_result_for_question("q1").evaluation.passed is True


def test_p99_helper_over_sample() -> None:
    """C1: P99 helper over a sample of measured cycle latencies."""
    samples: list[float] = []
    stub = DeterministicStubLLM()
    for _ in range(20):
        stub.reset()
        _, elapsed_ms, _ = measure_written_cycle_ms(llm=stub)
        samples.append(elapsed_ms)

    p99 = p99_ms(samples)
    assert len(samples) == 20
    assert min(samples) <= p99 <= max(samples)
    assert p99 < _SLO_Q_P99_TARGET_MS


def test_percentile_nearest_rank_unit() -> None:
    samples = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 100.0]
    assert percentile_nearest_rank(samples, 100.0) == 100.0
    assert p99_ms(samples) == 100.0
    assert percentile_nearest_rank(samples, 50.0) == 5.0


def test_percentile_rejects_empty_sample() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        p99_ms([])
