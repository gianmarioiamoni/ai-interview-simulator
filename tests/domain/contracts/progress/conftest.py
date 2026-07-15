# tests/domain/contracts/progress/conftest.py
# EPIC-02/P2-C2 — LearningProgress fixtures migrated to LongitudinalProfile input

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.contracts.progress.learning_progress import LearningProgress
from domain.contracts.progress.learning_progress_builder import LearningProgressBuilder

# Reuse longitudinal fixture helpers (P1 artefacts)
from tests.domain.contracts.longitudinal.conftest import (
    CANDIDATE_ID,
    SESSION_ID_0,
    SESSION_ID_1,
    FIXED_DT,
    make_longitudinal_profile,
    make_session_entry,
    make_candidate_profile_snapshot,
    make_session_metadata,
    make_profile_feature,
)
from domain.contracts.longitudinal.longitudinal_profile import (
    LongitudinalProfile,
    LongitudinalSessionEntry,
)

CANDIDATE_ID_B = "cand-test-002"
SESSION_ID = SESSION_ID_0
SESSION_ID_B = SESSION_ID_1
SESSION_ID_C = "sess-test-003"

FIXED_COMPUTED_AT = datetime(2026, 7, 3, 10, 0, 0, tzinfo=timezone.utc)


def make_single_entry_profile(
    candidate_id: str = CANDIDATE_ID,
    session_id: str = SESSION_ID,
    interview_index: int = 0,
) -> LongitudinalProfile:
    entry = make_session_entry(
        session_id=session_id,
        interview_index=interview_index,
        candidate_id=candidate_id,
    )
    return make_longitudinal_profile(candidate_id=candidate_id, entries=(entry,))


def make_two_entry_profile(
    candidate_id: str = CANDIDATE_ID,
) -> LongitudinalProfile:
    entry0 = make_session_entry(
        session_id=SESSION_ID, interview_index=0, candidate_id=candidate_id
    )
    entry1 = make_session_entry(
        session_id=SESSION_ID_B, interview_index=1, candidate_id=candidate_id,
        contributed_at=datetime(2026, 7, 14, 2, 0, 0, tzinfo=timezone.utc),
    )
    return make_longitudinal_profile(candidate_id=candidate_id, entries=(entry0, entry1))


def make_learning_progress(
    candidate_id: str = CANDIDATE_ID,
    profile: LongitudinalProfile | None = None,
) -> LearningProgress:
    resolved_profile = profile if profile is not None else make_two_entry_profile(candidate_id)
    return (
        LearningProgressBuilder()
        .with_longitudinal_profile(resolved_profile)
        .with_computed_at(FIXED_COMPUTED_AT)
        .build()
    )


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def candidate_id() -> str:
    return CANDIDATE_ID


@pytest.fixture
def single_entry_profile() -> LongitudinalProfile:
    return make_single_entry_profile()


@pytest.fixture
def two_entry_profile() -> LongitudinalProfile:
    return make_two_entry_profile()


@pytest.fixture
def learning_progress() -> LearningProgress:
    return make_learning_progress()


@pytest.fixture
def empty_progress() -> LearningProgress:
    return (
        LearningProgressBuilder()
        .with_candidate_identity_id(CANDIDATE_ID)
        .with_longitudinal_profile(None)
        .with_computed_at(FIXED_COMPUTED_AT)
        .build()
    )
