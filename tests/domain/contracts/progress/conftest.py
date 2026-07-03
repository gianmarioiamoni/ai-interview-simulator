# tests/domain/contracts/progress/conftest.py
# Shared fixtures for LearningProgress contract tests — reuses SessionHistory fixtures

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.contracts.progress.learning_progress import LearningProgress
from domain.contracts.progress.learning_progress_builder import LearningProgressBuilder
from domain.contracts.session_history.session_history import SessionHistory

# Reuse lower-layer fixture helpers
from tests.domain.contracts.session_history.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    make_session_history,
)

CANDIDATE_ID_B = "cand-test-002"
SESSION_ID_B = "sess-test-002"
SESSION_ID_C = "sess-test-003"

FIXED_COMPUTED_AT = datetime(2026, 7, 3, 10, 0, 0, tzinfo=timezone.utc)


def make_history(
    session_id: str = SESSION_ID,
    candidate_id: str = CANDIDATE_ID,
    interview_index: int = 0,
) -> SessionHistory:
    return make_session_history(
        session_id=session_id,
        candidate_id=candidate_id,
        interview_index=interview_index,
    )


def make_two_histories(candidate_id: str = CANDIDATE_ID) -> list[SessionHistory]:
    return [
        make_history(session_id=SESSION_ID, candidate_id=candidate_id, interview_index=0),
        make_history(session_id=SESSION_ID_B, candidate_id=candidate_id, interview_index=1),
    ]


def make_learning_progress(
    candidate_id: str = CANDIDATE_ID,
    histories: list[SessionHistory] | None = None,
) -> LearningProgress:
    if histories is None:
        histories = make_two_histories(candidate_id)
    return (
        LearningProgressBuilder()
        .with_candidate_identity_id(candidate_id)
        .with_session_histories(histories)
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
def single_history() -> SessionHistory:
    return make_history()


@pytest.fixture
def two_histories() -> list[SessionHistory]:
    return make_two_histories()


@pytest.fixture
def learning_progress() -> LearningProgress:
    return make_learning_progress()


@pytest.fixture
def empty_progress() -> LearningProgress:
    return (
        LearningProgressBuilder()
        .with_candidate_identity_id(CANDIDATE_ID)
        .with_session_histories([])
        .with_computed_at(FIXED_COMPUTED_AT)
        .build()
    )
