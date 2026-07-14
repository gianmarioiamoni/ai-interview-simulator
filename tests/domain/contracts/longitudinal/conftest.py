# tests/domain/contracts/longitudinal/conftest.py
# Shared fixtures for longitudinal contract tests (P1/C1)

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.feature.feature_quality import (
    FeatureConfidence,
    FeatureMaturity,
    FeatureQuality,
    FeatureStability,
)
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import CandidateProfileSnapshot
from domain.contracts.language.language_capability import LanguageCapability
from domain.contracts.longitudinal.longitudinal_profile import (
    CrossSessionLanguageCapability,
    LongitudinalProfile,
    LongitudinalSessionEntry,
    LongitudinalSessionMetadata,
)

CANDIDATE_ID = "cand-longitudinal-001"
SESSION_ID_0 = "sess-long-000"
SESSION_ID_1 = "sess-long-001"
FIXED_DT = datetime(2026, 7, 14, 0, 0, 0, tzinfo=timezone.utc)
LATER_DT = datetime(2026, 7, 14, 1, 0, 0, tzinfo=timezone.utc)


def make_profile_feature(candidate_id: str = CANDIDATE_ID, confidence: float = 0.7) -> ProfileFeature:
    identity = FeatureIdentity.for_type(FeatureType.REASONING)
    return ProfileFeature(
        feature_identity=identity,
        value="HIGH",
        quality=FeatureQuality(
            confidence=FeatureConfidence(value=confidence),
            stability=FeatureStability(state="stable"),
            maturity=FeatureMaturity.from_observation_count(3),
        ),
        provenance=FeatureProvenance(
            feature_identity=identity,
            source_observation_ids=("obs-1",),
            computed_at_question_index=3,
            feature_engine_version="1.0",
            updater_id="updater-reasoning",
        ),
        computed_at_question_index=3,
        candidate_identity_id=candidate_id,
    )


def make_candidate_profile_snapshot(candidate_id: str = CANDIDATE_ID) -> CandidateProfileSnapshot:
    feature = make_profile_feature(candidate_id=candidate_id)
    return CandidateProfileSnapshot(
        candidate_identity_id=candidate_id,
        features=(feature,),
        closed_at_question_index=5,
        source_observation_ids=("obs-1",),
        total_feature_count=1,
        mean_confidence=0.7,
    )


def make_session_metadata(knowledge_epoch: str = "1") -> LongitudinalSessionMetadata:
    return LongitudinalSessionMetadata(
        role="Backend Engineer",
        seniority="senior",
        interview_type="technical",
        question_count=5,
        session_language="en",
        knowledge_epoch=knowledge_epoch,
        total_objectives=2,
        total_narrative_insights=3,
        language_capabilities=(),
    )


def make_session_entry(
    session_id: str = SESSION_ID_0,
    interview_index: int = 0,
    candidate_id: str = CANDIDATE_ID,
    contributed_at: datetime = FIXED_DT,
    knowledge_epoch: str = "1",
) -> LongitudinalSessionEntry:
    return LongitudinalSessionEntry(
        session_id=session_id,
        interview_index=interview_index,
        profile_snapshot=make_candidate_profile_snapshot(candidate_id),
        session_metadata=make_session_metadata(knowledge_epoch=knowledge_epoch),
        contributed_at=contributed_at,
    )


def make_longitudinal_profile(
    candidate_id: str = CANDIDATE_ID,
    entries: tuple[LongitudinalSessionEntry, ...] | None = None,
    language_capability_summary: tuple[CrossSessionLanguageCapability, ...] = (),
) -> LongitudinalProfile:
    resolved_entries = entries if entries is not None else (make_session_entry(),)
    highest = max(resolved_entries, key=lambda e: e.interview_index)
    return LongitudinalProfile(
        candidate_identity_id=candidate_id,
        session_snapshots=resolved_entries,
        session_count=len(resolved_entries),
        language_capability_summary=language_capability_summary,
        knowledge_epoch=highest.session_metadata.knowledge_epoch,
        schema_version="1.0",
        created_at=FIXED_DT,
        last_updated_at=FIXED_DT,
    )


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def candidate_id() -> str:
    return CANDIDATE_ID


@pytest.fixture
def profile_snapshot() -> CandidateProfileSnapshot:
    return make_candidate_profile_snapshot()


@pytest.fixture
def session_metadata() -> LongitudinalSessionMetadata:
    return make_session_metadata()


@pytest.fixture
def session_entry() -> LongitudinalSessionEntry:
    return make_session_entry()


@pytest.fixture
def longitudinal_profile() -> LongitudinalProfile:
    return make_longitudinal_profile()


@pytest.fixture
def language_capability() -> LanguageCapability:
    return LanguageCapability(
        language_id="python",
        questions_answered_in_language=3,
        composite_score=0.8,
        idiomatic_usage_score=0.75,
        type_error_rate=0.1,
    )
