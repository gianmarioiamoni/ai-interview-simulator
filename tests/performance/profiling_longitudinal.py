# tests/performance/profiling_longitudinal.py
# EPIC-V13-09 C6 — longitudinal_update_node profiling (+ repo I/O)
# (AR-12, PROF-03/04). Harness-only; no cache / topology / state schema changes.

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, TypeVar

from app.graph.nodes.longitudinal_update_node import LongitudinalUpdateNode
from domain.contracts.interview_state import InterviewState
from domain.contracts.longitudinal.longitudinal_profile_builder import (
    LongitudinalProfileBuilder,
)
from infrastructure.longitudinal.longitudinal_profile_repository_impl import (
    JsonFileLongitudinalProfileRepository,
)
from tests.performance.helpers import measure_wall_clock_ms
from tests.performance.slo_r import (
    build_completed_state_for_slo_r,
    run_close_report_span,
)

T = TypeVar("T")


@dataclass(frozen=True)
class LongitudinalProfileEvidence:
    """Cross-session longitudinal update cost evidence (PROF-03 / AR-12)."""

    whole_node_ms: float
    repo_get_ms: float
    repo_save_ms: float
    profile_build_ms: float
    candidate_identity_id: str
    interview_index: int
    session_count_after: int
    had_prior_profile: bool
    profile_persisted: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_state_ready_for_longitudinal(
    *,
    interview_id: str = "epic09-c6-session",
    candidate_identity_id: str = "epic09-c6-candidate",
    interview_index: int = 0,
) -> InterviewState:
    """
    Closed session with materialized SessionHistory (close→report), ready for
    longitudinal_update. Harness wiring only (AR-22); no topology change.
    """
    completed = build_completed_state_for_slo_r(
        interview_id=interview_id,
        candidate_identity_id=candidate_identity_id,
    )
    state = run_close_report_span(completed)
    if state.session_history is None:
        raise RuntimeError("session_history missing after close→report")
    history = state.session_history.model_copy(
        update={
            "interview_index": interview_index,
            "session_id": interview_id,
            "candidate_identity_id": candidate_identity_id,
        }
    )
    return state.model_copy(
        update={
            "session_history": history,
            "candidate_identity_id": candidate_identity_id,
        }
    )


def _timed_call(label: str, bucket: dict[str, float], fn: Callable[[], T]) -> T:
    result, elapsed_ms = measure_wall_clock_ms(fn)
    bucket[label] = elapsed_ms
    return result


def profile_longitudinal_update(
    *,
    storage_dir: Path,
    state: InterviewState | None = None,
    interview_id: str = "epic09-c6-session",
    candidate_identity_id: str = "epic09-c6-candidate",
    interview_index: int = 0,
) -> tuple[LongitudinalProfileEvidence, InterviewState]:
    """
    Profile ``longitudinal_update_node`` whole-node + repo I/O + profile build.

    Uses real ``JsonFileLongitudinalProfileRepository`` (no LongitudinalProfile
    cache — AR-07 rejected). Measurement owned by harness timers (PROF-04).
    """
    base_state = (
        state
        if state is not None
        else build_state_ready_for_longitudinal(
            interview_id=interview_id,
            candidate_identity_id=candidate_identity_id,
            interview_index=interview_index,
        )
    )
    if base_state.session_history is None:
        raise RuntimeError("session_history required for longitudinal profiling")

    repo = JsonFileLongitudinalProfileRepository(storage_dir=storage_dir)
    had_prior = repo.exists(base_state.session_history.candidate_identity_id)
    stage_ms: dict[str, float] = {}

    original_get = repo.get
    original_save = repo.save
    original_build = LongitudinalProfileBuilder.build

    def timed_get(candidate_id: str) -> object:
        return _timed_call("repo_get", stage_ms, lambda: original_get(candidate_id))

    def timed_save(profile: object) -> None:
        _timed_call("repo_save", stage_ms, lambda: original_save(profile))

    def timed_build(builder: LongitudinalProfileBuilder) -> object:
        return _timed_call("profile_build", stage_ms, lambda: original_build(builder))

    repo.get = timed_get  # type: ignore[method-assign]
    repo.save = timed_save  # type: ignore[method-assign]
    LongitudinalProfileBuilder.build = timed_build  # type: ignore[method-assign]

    node = LongitudinalUpdateNode(repository=repo)
    try:
        result_state, whole_node_ms = measure_wall_clock_ms(lambda: node(base_state))
    finally:
        repo.get = original_get  # type: ignore[method-assign]
        repo.save = original_save  # type: ignore[method-assign]
        LongitudinalProfileBuilder.build = original_build  # type: ignore[method-assign]

    required = ("repo_get", "repo_save", "profile_build")
    missing = [name for name in required if name not in stage_ms]
    if missing:
        raise RuntimeError(
            f"Longitudinal stage timers missing after update: {missing}"
        )

    candidate_id = base_state.session_history.candidate_identity_id
    persisted = repo.get(candidate_id)
    if persisted is None:
        raise RuntimeError("longitudinal profile was not persisted after update")

    evidence = LongitudinalProfileEvidence(
        whole_node_ms=whole_node_ms,
        repo_get_ms=stage_ms["repo_get"],
        repo_save_ms=stage_ms["repo_save"],
        profile_build_ms=stage_ms["profile_build"],
        candidate_identity_id=candidate_id,
        interview_index=base_state.session_history.interview_index,
        session_count_after=persisted.session_count,
        had_prior_profile=had_prior,
        profile_persisted=True,
    )
    return evidence, result_state
