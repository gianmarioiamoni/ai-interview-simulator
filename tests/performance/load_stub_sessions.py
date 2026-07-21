# tests/performance/load_stub_sessions.py
# EPIC-V13-09 C7/C8 — stub-LLM load runner, absolute SLO gates, early/late
# degradation (LOAD-01–05, AR-15/16). Harness-only.

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from unittest.mock import MagicMock

from app.graph.interview_graph import build_interview_graph
from tests.factories.interview_state_factory import build_written_question_state
from tests.performance.helpers import measure_wall_clock_ms, p99_ms
from tests.performance.slo_r import (
    SLO_R_TARGET_MS,
    build_completed_state_for_slo_r,
    run_close_report_span,
)
from tests.performance.stub_llm import DeterministicStubLLM

# Implementation Plan §3 / Freeze AR-01/AR-03 absolute targets.
LOAD_SESSION_COUNT = 50
WRITTEN_QUESTIONS_PER_SESSION = 5
SLO_Q_P99_TARGET_MS = 8000.0
# Re-export for load callers.
SLO_R_ABS_TARGET_MS = SLO_R_TARGET_MS

# C8 / LOAD-03 — Implementation Plan §3 windows + ratio.
EARLY_WINDOW_START = 1
EARLY_WINDOW_END = 10
LATE_WINDOW_START = 41
LATE_WINDOW_END = 50
DEGRADATION_RATIO_MAX = 1.25


@dataclass(frozen=True)
class SessionLoadResult:
    """One synthetic written-heavy session under stub load."""

    session_index: int  # 1-based (LOAD-01 ordering)
    slo_q_samples_ms: tuple[float, ...]
    slo_r_ms: float
    hard_failure: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.hard_failure is None


@dataclass(frozen=True)
class StubLoadRunResult:
    """Aggregate 50-session stub-LLM load evidence (C7 absolute gates)."""

    sessions: tuple[SessionLoadResult, ...]
    session_count: int = LOAD_SESSION_COUNT
    questions_per_session: int = WRITTEN_QUESTIONS_PER_SESSION

    def all_slo_q_ms(self) -> list[float]:
        samples: list[float] = []
        for session in self.sessions:
            if session.succeeded:
                samples.extend(session.slo_q_samples_ms)
        return samples

    def all_slo_r_ms(self) -> list[float]:
        return [s.slo_r_ms for s in self.sessions if s.succeeded]

    def hard_failure_count(self) -> int:
        return sum(1 for s in self.sessions if not s.succeeded)

    def slo_q_p99_ms(self) -> float:
        return p99_ms(self.all_slo_q_ms())

    def slo_r_max_ms(self) -> float:
        samples = self.all_slo_r_ms()
        if not samples:
            raise ValueError("no successful SLO-R samples")
        return max(samples)

    def sessions_in_window(
        self,
        start: int,
        end: int,
    ) -> tuple[SessionLoadResult, ...]:
        """Inclusive 1-based session_index window (LOAD-03)."""
        return tuple(
            s for s in self.sessions if start <= s.session_index <= end and s.succeeded
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "session_count": self.session_count,
            "questions_per_session": self.questions_per_session,
            "hard_failure_count": self.hard_failure_count(),
            "slo_q_sample_count": len(self.all_slo_q_ms()),
            "slo_q_p99_ms": self.slo_q_p99_ms() if self.all_slo_q_ms() else None,
            "slo_r_max_ms": self.slo_r_max_ms() if self.all_slo_r_ms() else None,
            "sessions": [asdict(s) for s in self.sessions],
        }
        if self.session_count >= LATE_WINDOW_END:
            payload["degradation"] = analyze_degradation(self).to_dict()
        return payload


@dataclass(frozen=True)
class WindowMetrics:
    """SLO metrics for one early/late session window."""

    start: int
    end: int
    session_count: int
    slo_q_p99_ms: float
    slo_r_max_ms: float


@dataclass(frozen=True)
class DegradationAnalysis:
    """Early vs late degradation evidence (LOAD-03 / C8)."""

    early: WindowMetrics
    late: WindowMetrics
    slo_q_ratio: float
    slo_r_ratio: float
    ratio_limit: float = DEGRADATION_RATIO_MAX

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _window_metrics(
    result: StubLoadRunResult,
    *,
    start: int,
    end: int,
) -> WindowMetrics:
    window = result.sessions_in_window(start, end)
    expected = end - start + 1
    if len(window) != expected:
        raise ValueError(
            f"window {start}-{end}: expected {expected} successful sessions, "
            f"got {len(window)}"
        )
    slo_q: list[float] = []
    slo_r: list[float] = []
    for session in window:
        slo_q.extend(session.slo_q_samples_ms)
        slo_r.append(session.slo_r_ms)
    return WindowMetrics(
        start=start,
        end=end,
        session_count=len(window),
        slo_q_p99_ms=p99_ms(slo_q),
        slo_r_max_ms=max(slo_r),
    )


def _degradation_ratio(late_ms: float, early_ms: float) -> float:
    if early_ms <= 0.0:
        if late_ms <= 0.0:
            return 1.0
        raise ValueError(
            "early-window metric is zero; cannot compute degradation ratio"
        )
    return late_ms / early_ms


def analyze_degradation(result: StubLoadRunResult) -> DegradationAnalysis:
    """Compute early (1–10) vs late (41–50) SLO-Q P99 and SLO-R max ratios."""
    if result.session_count < LATE_WINDOW_END:
        raise ValueError(
            f"degradation analysis requires >= {LATE_WINDOW_END} sessions, "
            f"got {result.session_count}"
        )
    early = _window_metrics(
        result, start=EARLY_WINDOW_START, end=EARLY_WINDOW_END
    )
    late = _window_metrics(
        result, start=LATE_WINDOW_START, end=LATE_WINDOW_END
    )
    return DegradationAnalysis(
        early=early,
        late=late,
        slo_q_ratio=_degradation_ratio(late.slo_q_p99_ms, early.slo_q_p99_ms),
        slo_r_ratio=_degradation_ratio(late.slo_r_max_ms, early.slo_r_max_ms),
    )


def _measure_written_cycle_on_graph(
    graph: object,
    stub: DeterministicStubLLM,
) -> float:
    # Rewind scripted responses without clearing invoke_call_count (LOAD-05 evidence).
    stub._index = 0
    state = build_written_question_state()
    _, elapsed_ms = measure_wall_clock_ms(lambda: graph.invoke(state))
    return elapsed_ms


def _run_one_session(
    *,
    session_index: int,
    graph: object,
    stub: DeterministicStubLLM,
) -> SessionLoadResult:
    try:
        slo_q_samples: list[float] = []
        for _ in range(WRITTEN_QUESTIONS_PER_SESSION):
            slo_q_samples.append(_measure_written_cycle_on_graph(graph, stub))

        completed = build_completed_state_for_slo_r(
            n_questions=WRITTEN_QUESTIONS_PER_SESSION,
            interview_id=f"epic09-c7-session-{session_index:02d}",
            candidate_identity_id=f"epic09-c7-candidate-{session_index:02d}",
        )
        _, slo_r_ms = measure_wall_clock_ms(lambda: run_close_report_span(completed))

        return SessionLoadResult(
            session_index=session_index,
            slo_q_samples_ms=tuple(slo_q_samples),
            slo_r_ms=slo_r_ms,
            hard_failure=None,
        )
    except Exception as exc:  # noqa: BLE001 — load harness counts hard failures
        return SessionLoadResult(
            session_index=session_index,
            slo_q_samples_ms=(),
            slo_r_ms=-1.0,
            hard_failure=f"{type(exc).__name__}: {exc}",
        )


def run_stub_load(
    *,
    session_count: int = LOAD_SESSION_COUNT,
    llm: DeterministicStubLLM | None = None,
) -> StubLoadRunResult:
    """
    Run consecutive stub-LLM sessions (LOAD-01/02/05).

    Each session: 5 written ``graph.invoke`` cycles (SLO-Q) + one close→report
    span (SLO-R). Absolute SLO gates and hard-failure count are asserted by
    tests; early/late degradation ratio is C8 (LOAD-03).
    """
    if session_count < 1:
        raise ValueError("session_count must be >= 1")

    stub = llm if llm is not None else DeterministicStubLLM()
    graph = build_interview_graph(llm=stub, hint_service=MagicMock())

    sessions: list[SessionLoadResult] = []
    for index in range(1, session_count + 1):
        sessions.append(
            _run_one_session(session_index=index, graph=graph, stub=stub)
        )

    return StubLoadRunResult(sessions=tuple(sessions), session_count=session_count)


def assert_absolute_load_slos(result: StubLoadRunResult) -> None:
    """C7 absolute gates: zero hard failures; SLO-Q P99 < 8s; SLO-R max < 3s."""
    if result.hard_failure_count() != 0:
        failures = [s for s in result.sessions if not s.succeeded]
        raise AssertionError(
            f"LOAD-04 violated: {result.hard_failure_count()} hard failures; "
            f"first={failures[0].hard_failure}"
        )

    expected_q = result.session_count * WRITTEN_QUESTIONS_PER_SESSION
    samples_q = result.all_slo_q_ms()
    if len(samples_q) != expected_q:
        raise AssertionError(
            f"expected {expected_q} SLO-Q samples, got {len(samples_q)}"
        )

    q_p99 = result.slo_q_p99_ms()
    if q_p99 >= SLO_Q_P99_TARGET_MS:
        raise AssertionError(
            f"SLO-Q P99 {q_p99:.2f}ms >= target {SLO_Q_P99_TARGET_MS:.0f}ms"
        )

    r_max = result.slo_r_max_ms()
    if r_max >= SLO_R_ABS_TARGET_MS:
        raise AssertionError(
            f"SLO-R max {r_max:.2f}ms >= target {SLO_R_ABS_TARGET_MS:.0f}ms"
        )


def assert_degradation_gate(result: StubLoadRunResult) -> DegradationAnalysis:
    """
    C8 / LOAD-03: late/early ≤ 1.25 for SLO-Q P99 and SLO-R max, and late
    window still meets absolute SLO targets (8s / 3s).
    """
    analysis = analyze_degradation(result)

    if analysis.late.slo_q_p99_ms >= SLO_Q_P99_TARGET_MS:
        raise AssertionError(
            f"late-window SLO-Q P99 {analysis.late.slo_q_p99_ms:.2f}ms "
            f">= target {SLO_Q_P99_TARGET_MS:.0f}ms"
        )
    if analysis.late.slo_r_max_ms >= SLO_R_ABS_TARGET_MS:
        raise AssertionError(
            f"late-window SLO-R max {analysis.late.slo_r_max_ms:.2f}ms "
            f">= target {SLO_R_ABS_TARGET_MS:.0f}ms"
        )
    if analysis.slo_q_ratio > DEGRADATION_RATIO_MAX:
        raise AssertionError(
            f"SLO-Q late/early ratio {analysis.slo_q_ratio:.3f} "
            f"> {DEGRADATION_RATIO_MAX}"
        )
    if analysis.slo_r_ratio > DEGRADATION_RATIO_MAX:
        raise AssertionError(
            f"SLO-R late/early ratio {analysis.slo_r_ratio:.3f} "
            f"> {DEGRADATION_RATIO_MAX}"
        )
    return analysis
