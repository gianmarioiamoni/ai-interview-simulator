# tests/integration/test_progress_tracker_p5_c2.py
# EPIC-02/P5-C2 — End-to-end integration test: 3-session synthetic run
#
# Test plan (EPIC-02-IMPLEMENTATION-PLAN.md §8 integration tests — "3-session synthetic run"):
#   - Profile accumulates 3 entries after 3 longitudinal saves.
#   - LearningProgress derived by ProgressTracker has has_sufficient_data=True.
#   - BehavioralTrend is present and non-empty.
#   - session_entries count == 3.
#   - Candidate identity consistent across all sessions.
#   - LearningProgress is NOT persisted (LP-LP-06): only one JSON file per candidate.
#
# Architectural tests verified here:
#   LP-08: Reconstruction — 10-session synthetic dataset.
#   LP-11: Replay independence — import graph analysis.

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pytest

from domain.contracts.longitudinal.longitudinal_profile import LongitudinalProfile
from domain.contracts.longitudinal.longitudinal_profile_builder import (
    LongitudinalProfileBuilder,
)
from domain.contracts.longitudinal.longitudinal_profile_repository import (
    LongitudinalProfileRepository,
)
from domain.contracts.session_history.session_history import SessionHistory
from infrastructure.longitudinal.longitudinal_profile_repository_impl import (
    JsonFileLongitudinalProfileRepository,
)
from services.progress.progress_tracker import ProgressTracker
from tests.domain.contracts.knowledge_snapshot.conftest import make_knowledge_snapshot
from tests.domain.contracts.session_history.conftest import (
    make_interview_metadata,
    make_language_profile,
    make_session_history,
    make_transcript,
    make_question_timeline,
)
from domain.contracts.session_history.session_history import ReplayMetadata
from domain.contracts.session_history.session_history_builder import SessionHistoryBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CANDIDATE_ID_3 = "cand-p5-three-session"
CANDIDATE_ID_10 = "cand-p5-ten-session"
FIXED_BASE_TS = datetime(2026, 7, 14, 0, 0, 0, tzinfo=timezone.utc)


def _make_session_history(
    candidate_id: str,
    session_id: str,
    interview_index: int,
) -> SessionHistory:
    """Synthetic SessionHistory for integration tests."""
    snapshot = make_knowledge_snapshot(
        session_id=session_id,
        candidate_id=candidate_id,
    )
    return (
        SessionHistoryBuilder()
        .with_session_id(session_id)
        .with_candidate_identity_id(candidate_id)
        .with_interview_index(interview_index)
        .with_knowledge_snapshot(snapshot)
        .with_interview_metadata(make_interview_metadata())
        .with_language_profile(make_language_profile(session_id=session_id))
        .with_transcript(make_transcript())
        .with_question_timeline(make_question_timeline())
        .with_replay_metadata(ReplayMetadata(snapshot_is_complete=True))
        .with_created_at(FIXED_BASE_TS)
        .build()
    )


def _accumulate_sessions(
    candidate_id: str,
    session_count: int,
    repository: LongitudinalProfileRepository,
) -> LongitudinalProfile:
    """Run `session_count` sessions through LongitudinalProfileBuilder + repository.save()."""
    prior: Optional[LongitudinalProfile] = None

    for i in range(session_count):
        session_id = f"sess-{candidate_id}-{i:03d}"
        session_history = _make_session_history(
            candidate_id=candidate_id,
            session_id=session_id,
            interview_index=i,
        )
        ts = datetime(2026, 7, 14, i, 0, 0, tzinfo=timezone.utc)
        profile = (
            LongitudinalProfileBuilder()
            .with_prior_profile(prior)
            .with_session_history(session_history)
            .with_language_capabilities(())
            .with_current_timestamp(ts)
            .build()
        )
        repository.save(profile)
        prior = profile

    final = repository.get(candidate_id)
    assert final is not None
    return final


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def repo(tmp_path: Path) -> JsonFileLongitudinalProfileRepository:
    return JsonFileLongitudinalProfileRepository(
        storage_dir=tmp_path / "longitudinal_p5"
    )


# ---------------------------------------------------------------------------
# 3-session synthetic run (P5-C2 integration test)
# ---------------------------------------------------------------------------


class TestThreeSessionSyntheticRun:
    """3-session synthetic run verifies profile accumulation and LearningProgress consistency."""

    def test_profile_session_count_is_three(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        profile = _accumulate_sessions(CANDIDATE_ID_3, 3, repo)
        assert profile.session_count == 3

    def test_profile_snapshot_count_is_three(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        profile = _accumulate_sessions(CANDIDATE_ID_3, 3, repo)
        assert len(profile.session_snapshots) == 3

    def test_profile_candidate_identity_id(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        profile = _accumulate_sessions(CANDIDATE_ID_3, 3, repo)
        assert profile.candidate_identity_id == CANDIDATE_ID_3

    def test_progress_has_sufficient_data_true(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        _accumulate_sessions(CANDIDATE_ID_3, 3, repo)
        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID_3)
        assert progress.has_sufficient_data is True

    def test_progress_session_entries_count(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        _accumulate_sessions(CANDIDATE_ID_3, 3, repo)
        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID_3)
        assert len(progress.session_entries) == 3

    def test_progress_behavioral_trend_present(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        _accumulate_sessions(CANDIDATE_ID_3, 3, repo)
        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID_3)
        assert progress.behavioral_trend is not None

    def test_progress_behavioral_trend_sessions_analysed(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        _accumulate_sessions(CANDIDATE_ID_3, 3, repo)
        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID_3)
        assert progress.behavioral_trend is not None
        assert progress.behavioral_trend.sessions_analysed == 3

    def test_progress_candidate_identity_id(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        _accumulate_sessions(CANDIDATE_ID_3, 3, repo)
        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID_3)
        assert progress.candidate_identity_id == CANDIDATE_ID_3

    def test_learning_progress_not_persisted(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        """LP-LP-06: LearningProgress is never written to the repository.

        After 3 accumulation saves, the repository contains exactly 1 file
        (the candidate's LongitudinalProfile). No LearningProgress file exists.
        """
        _accumulate_sessions(CANDIDATE_ID_3, 3, repo)
        tracker = ProgressTracker(repository=repo)
        tracker.get_progress(CANDIDATE_ID_3)
        storage_dir = repo._storage_dir
        stored_files = list(storage_dir.glob("*.json"))
        assert len(stored_files) == 1
        assert stored_files[0].stem == CANDIDATE_ID_3


# ---------------------------------------------------------------------------
# LP-08: Reconstruction — 10-session synthetic dataset
# ---------------------------------------------------------------------------


class TestLP08Reconstruction:
    """LP-08: Reconstruct LongitudinalProfile from 10 synthetic sessions.

    Verifies iterative LongitudinalProfileBuilder produces a profile consistent
    with direct session data. language_capability_summary asserted [] (V1.3 gap).
    """

    def test_reconstruction_session_count(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        profile = _accumulate_sessions(CANDIDATE_ID_10, 10, repo)
        assert profile.session_count == 10

    def test_reconstruction_all_snapshots_present(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        profile = _accumulate_sessions(CANDIDATE_ID_10, 10, repo)
        assert len(profile.session_snapshots) == 10

    def test_reconstruction_interview_indices_sequential(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        profile = _accumulate_sessions(CANDIDATE_ID_10, 10, repo)
        indices = [e.interview_index for e in profile.session_snapshots]
        assert indices == list(range(10))

    def test_reconstruction_language_capability_summary_empty(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        """V1.3 accepted gap: language_capabilities are transient (DATA-MODEL.md §6.3)."""
        profile = _accumulate_sessions(CANDIDATE_ID_10, 10, repo)
        assert profile.language_capability_summary == ()

    def test_reconstruction_candidate_identity_id(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        profile = _accumulate_sessions(CANDIDATE_ID_10, 10, repo)
        assert profile.candidate_identity_id == CANDIDATE_ID_10

    def test_reconstruction_schema_version(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        profile = _accumulate_sessions(CANDIDATE_ID_10, 10, repo)
        assert profile.schema_version == "1.0"

    def test_reconstruction_progress_has_sufficient_data(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        _accumulate_sessions(CANDIDATE_ID_10, 10, repo)
        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID_10)
        assert progress.has_sufficient_data is True

    def test_reconstruction_progress_session_entries_count(self, repo: JsonFileLongitudinalProfileRepository) -> None:
        _accumulate_sessions(CANDIDATE_ID_10, 10, repo)
        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID_10)
        assert len(progress.session_entries) == 10


# ---------------------------------------------------------------------------
# LP-11: Replay independence — import graph analysis
# ---------------------------------------------------------------------------


class TestLP11ReplayIndependence:
    """LP-11: No replay contract imports LongitudinalProfile; no LongitudinalProfile imports replay."""

    LONGITUDINAL_MODULES = [
        "domain.contracts.longitudinal.longitudinal_profile",
        "domain.contracts.longitudinal.longitudinal_profile_builder",
        "domain.contracts.longitudinal.longitudinal_profile_repository",
    ]

    REPLAY_KEYWORDS = [
        "replay",
        "ReplayMetadata",
        "ReplaySnapshot",
        "replay_contract",
    ]

    def _get_module_source(self, module_name: str) -> str:
        spec = importlib.util.find_spec(module_name)
        if spec is None or spec.origin is None:
            return ""
        return Path(spec.origin).read_text(encoding="utf-8")

    def test_longitudinal_profile_does_not_import_replay(self) -> None:
        """LongitudinalProfile module must not import any replay contract."""
        for module_name in self.LONGITUDINAL_MODULES:
            source = self._get_module_source(module_name)
            for keyword in self.REPLAY_KEYWORDS:
                assert keyword not in source, (
                    f"LP-11 violation: {module_name} imports replay keyword '{keyword}'"
                )

    def test_progress_tracker_does_not_import_replay(self) -> None:
        """ProgressTracker must not import any replay contract."""
        source = self._get_module_source("services.progress.progress_tracker")
        for keyword in self.REPLAY_KEYWORDS:
            assert keyword not in source, (
                f"LP-11 violation: services.progress.progress_tracker imports "
                f"replay keyword '{keyword}'"
            )

    def test_replay_contracts_do_not_import_longitudinal(self) -> None:
        """Replay contracts must not import LongitudinalProfile."""
        longitudinal_keywords = [
            "LongitudinalProfile",
            "longitudinal_profile",
            "LongitudinalProfileBuilder",
            "LongitudinalProfileRepository",
        ]
        domain_root = Path(__file__).parent.parent.parent / "domain"
        replay_files = [
            f for f in domain_root.rglob("*replay*")
            if f.is_file() and f.suffix == ".py"
        ]
        session_history_files = list(domain_root.rglob("session_history*.py"))

        candidate_files = [f for f in replay_files + session_history_files if f.is_file()]
        for fpath in candidate_files:
            source = fpath.read_text(encoding="utf-8")
            for keyword in longitudinal_keywords:
                assert keyword not in source, (
                    f"LP-11 violation: {fpath} imports longitudinal keyword '{keyword}'"
                )
