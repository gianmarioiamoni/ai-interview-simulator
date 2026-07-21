# tests/performance/test_profiling_longitudinal.py
# EPIC-V13-09 C6 — PROF-03: longitudinal_update (+ repo I/O) cross-session profiling.

from __future__ import annotations

from pathlib import Path

from domain.contracts.longitudinal.longitudinal_profile_builder import (
    LongitudinalProfileBuilder,
)
from infrastructure.longitudinal.longitudinal_profile_repository_impl import (
    JsonFileLongitudinalProfileRepository,
)
from tests.performance.profiling_longitudinal import (
    LongitudinalProfileEvidence,
    build_state_ready_for_longitudinal,
    profile_longitudinal_update,
)


def test_longitudinal_whole_node_and_repo_io_are_profiled(tmp_path: Path) -> None:
    """PROF-03 / AR-12: whole-node + repo get/save + profile build timings."""
    evidence, state = profile_longitudinal_update(
        storage_dir=tmp_path / "longitudinal",
        candidate_identity_id="c6-candidate-a",
        interview_id="c6-session-0",
        interview_index=0,
    )

    assert isinstance(evidence, LongitudinalProfileEvidence)
    assert evidence.whole_node_ms >= 0.0
    assert evidence.repo_get_ms >= 0.0
    assert evidence.repo_save_ms >= 0.0
    assert evidence.profile_build_ms >= 0.0
    assert evidence.had_prior_profile is False
    assert evidence.profile_persisted is True
    assert evidence.session_count_after == 1
    assert state.session_history is not None


def test_cross_session_update_loads_prior_and_persists(tmp_path: Path) -> None:
    """PROF-03: second session exercises prior-profile load (cross-session cost)."""
    storage = tmp_path / "longitudinal"
    first, _ = profile_longitudinal_update(
        storage_dir=storage,
        candidate_identity_id="c6-candidate-b",
        interview_id="c6-session-0",
        interview_index=0,
    )
    second, _ = profile_longitudinal_update(
        storage_dir=storage,
        candidate_identity_id="c6-candidate-b",
        interview_id="c6-session-1",
        interview_index=1,
    )

    assert first.had_prior_profile is False
    assert second.had_prior_profile is True
    assert second.session_count_after == 2
    assert second.repo_get_ms >= 0.0
    assert second.repo_save_ms >= 0.0
    assert second.whole_node_ms >= 0.0


def test_evidence_payload_includes_cross_session_fields(tmp_path: Path) -> None:
    """Evidence artifact suitable for baseline report (PROF-03)."""
    evidence, _ = profile_longitudinal_update(storage_dir=tmp_path / "longitudinal")
    payload = evidence.to_dict()

    assert "whole_node_ms" in payload
    assert "repo_get_ms" in payload
    assert "repo_save_ms" in payload
    assert "profile_build_ms" in payload
    assert "had_prior_profile" in payload
    assert "session_count_after" in payload
    assert payload["profile_persisted"] is True


def test_profiling_harness_restores_builder_wrapper(tmp_path: Path) -> None:
    """Harness timers must not leave LongitudinalProfileBuilder.build patched."""
    original_build = LongitudinalProfileBuilder.build
    profile_longitudinal_update(storage_dir=tmp_path / "longitudinal")
    assert LongitudinalProfileBuilder.build is original_build


def test_no_longitudinal_profile_cache_layer(tmp_path: Path) -> None:
    """AR-07 rejected: harness uses file repository only (no cache)."""
    storage = tmp_path / "longitudinal"
    evidence, _ = profile_longitudinal_update(storage_dir=storage)
    repo = JsonFileLongitudinalProfileRepository(storage_dir=storage)
    assert repo.exists(evidence.candidate_identity_id) is True
    assert (storage / f"{evidence.candidate_identity_id}.json").is_file()


def test_build_state_ready_for_longitudinal_has_session_history() -> None:
    state = build_state_ready_for_longitudinal(
        interview_id="c6-ready",
        candidate_identity_id="c6-ready-candidate",
        interview_index=0,
    )
    assert state.session_history is not None
    assert state.session_history.candidate_identity_id == "c6-ready-candidate"
    assert state.report is not None
