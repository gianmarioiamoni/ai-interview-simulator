# tests/services/progress/test_progress_tracker_p5.py
# EPIC-02/P5-C1 — ProgressTracker unit tests
#
# Test plan (EPIC-02-IMPLEMENTATION-PLAN.md §5 P5-C1):
#   - Returns LearningProgress with has_sufficient_data=False for one-session profile.
#   - Returns LearningProgress with trend data and has_sufficient_data=True for two-session profile.
#   - Returns LearningProgress with has_sufficient_data=False when no profile found (None).

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from domain.contracts.longitudinal.longitudinal_profile_repository import (
    LongitudinalProfileRepository,
)
from services.progress.progress_tracker import ProgressTracker
from tests.domain.contracts.longitudinal.conftest import (
    CANDIDATE_ID,
    make_session_entry,
    make_longitudinal_profile,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_one_session_profile() -> object:
    return make_longitudinal_profile(
        candidate_id=CANDIDATE_ID,
        entries=(make_session_entry(session_id="sess-0", interview_index=0),),
    )


def make_two_session_profile() -> object:
    entry0 = make_session_entry(session_id="sess-0", interview_index=0)
    entry1 = make_session_entry(
        session_id="sess-1",
        interview_index=1,
        contributed_at=datetime(2026, 7, 14, 2, 0, 0, tzinfo=timezone.utc),
    )
    return make_longitudinal_profile(
        candidate_id=CANDIDATE_ID,
        entries=(entry0, entry1),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestProgressTrackerOneSession:
    """ProgressTracker returns has_sufficient_data=False for a one-session profile."""

    def test_one_session_has_sufficient_data_false(self) -> None:
        repo = MagicMock(spec=LongitudinalProfileRepository)
        repo.get.return_value = make_one_session_profile()

        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID)

        assert progress.has_sufficient_data is False

    def test_one_session_entries_not_empty(self) -> None:
        repo = MagicMock(spec=LongitudinalProfileRepository)
        repo.get.return_value = make_one_session_profile()

        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID)

        assert len(progress.session_entries) == 1

    def test_one_session_candidate_identity_id(self) -> None:
        repo = MagicMock(spec=LongitudinalProfileRepository)
        repo.get.return_value = make_one_session_profile()

        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID)

        assert progress.candidate_identity_id == CANDIDATE_ID


class TestProgressTrackerTwoSessions:
    """ProgressTracker returns trend data and has_sufficient_data=True for two-session profile."""

    def test_two_sessions_has_sufficient_data_true(self) -> None:
        repo = MagicMock(spec=LongitudinalProfileRepository)
        repo.get.return_value = make_two_session_profile()

        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID)

        assert progress.has_sufficient_data is True

    def test_two_sessions_behavioral_trend_present(self) -> None:
        repo = MagicMock(spec=LongitudinalProfileRepository)
        repo.get.return_value = make_two_session_profile()

        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID)

        assert progress.behavioral_trend is not None

    def test_two_sessions_entries_count(self) -> None:
        repo = MagicMock(spec=LongitudinalProfileRepository)
        repo.get.return_value = make_two_session_profile()

        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID)

        assert len(progress.session_entries) == 2

    def test_two_sessions_candidate_identity_id(self) -> None:
        repo = MagicMock(spec=LongitudinalProfileRepository)
        repo.get.return_value = make_two_session_profile()

        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID)

        assert progress.candidate_identity_id == CANDIDATE_ID


class TestProgressTrackerNoProfile:
    """ProgressTracker returns empty LearningProgress when no profile found."""

    def test_no_profile_has_sufficient_data_false(self) -> None:
        repo = MagicMock(spec=LongitudinalProfileRepository)
        repo.get.return_value = None

        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID)

        assert progress.has_sufficient_data is False

    def test_no_profile_empty_entries(self) -> None:
        repo = MagicMock(spec=LongitudinalProfileRepository)
        repo.get.return_value = None

        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID)

        assert progress.session_entries == ()

    def test_no_profile_behavioral_trend_none(self) -> None:
        repo = MagicMock(spec=LongitudinalProfileRepository)
        repo.get.return_value = None

        tracker = ProgressTracker(repository=repo)
        progress = tracker.get_progress(CANDIDATE_ID)

        assert progress.behavioral_trend is None

    def test_repository_get_called_once(self) -> None:
        repo = MagicMock(spec=LongitudinalProfileRepository)
        repo.get.return_value = None

        tracker = ProgressTracker(repository=repo)
        tracker.get_progress(CANDIDATE_ID)

        repo.get.assert_called_once_with(CANDIDATE_ID)
