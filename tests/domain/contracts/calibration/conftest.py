# tests/domain/contracts/calibration/conftest.py
# Shared fixtures for Calibration contract tests — reuses LearningProgress + SessionHistory fixtures

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.contracts.calibration.calibration_builder import CalibrationBuilder
from domain.contracts.calibration.calibration_profile import CalibrationProfile
from domain.contracts.calibration.calibration_snapshot import CalibrationSnapshot
from domain.contracts.progress.learning_progress import LearningProgress

from tests.domain.contracts.progress.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    SESSION_ID_B,
    FIXED_COMPUTED_AT,
    make_learning_progress,
    make_two_histories,
    make_history,
)
from tests.domain.contracts.knowledge_snapshot.conftest import (
    make_knowledge_snapshot,
)

ROLE = "Software Engineer"
SENIORITY = "Senior"


def make_calibration_profile(
    candidate_id: str = CANDIDATE_ID,
    role: str = ROLE,
    seniority: str = SENIORITY,
    progress: LearningProgress | None = None,
) -> CalibrationProfile:
    if progress is None:
        progress = make_learning_progress(candidate_id=candidate_id)
    return (
        CalibrationBuilder()
        .with_candidate_identity_id(candidate_id)
        .with_role(role)
        .with_seniority(seniority)
        .with_learning_progress(progress)
        .with_computed_at(FIXED_COMPUTED_AT)
        .build_profile()
    )


def make_calibration_snapshot(
    candidate_id: str = CANDIDATE_ID,
    session_id: str = SESSION_ID,
    role: str = ROLE,
    seniority: str = SENIORITY,
    progress: LearningProgress | None = None,
) -> CalibrationSnapshot:
    if progress is None:
        progress = make_learning_progress(candidate_id=candidate_id)
    ks = make_knowledge_snapshot(session_id=session_id, candidate_id=candidate_id)
    return (
        CalibrationBuilder()
        .with_candidate_identity_id(candidate_id)
        .with_role(role)
        .with_seniority(seniority)
        .with_learning_progress(progress)
        .with_knowledge_snapshot(ks)
        .with_computed_at(FIXED_COMPUTED_AT)
        .build_snapshot()
    )


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def candidate_id() -> str:
    return CANDIDATE_ID


@pytest.fixture
def learning_progress() -> LearningProgress:
    return make_learning_progress()


@pytest.fixture
def calibration_profile() -> CalibrationProfile:
    return make_calibration_profile()


@pytest.fixture
def calibration_snapshot() -> CalibrationSnapshot:
    return make_calibration_snapshot()


@pytest.fixture
def empty_progress_profile() -> CalibrationProfile:
    from domain.contracts.progress.learning_progress_builder import LearningProgressBuilder
    empty = (
        LearningProgressBuilder()
        .with_candidate_identity_id(CANDIDATE_ID)
        .with_session_histories([])
        .with_computed_at(FIXED_COMPUTED_AT)
        .build()
    )
    return make_calibration_profile(progress=empty)
