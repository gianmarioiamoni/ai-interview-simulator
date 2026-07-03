# tests/domain/contracts/knowledge_snapshot/conftest.py
# Shared fixtures for KnowledgeSnapshot contract tests

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.contracts.coaching.coaching_builder import CoachingBuilder, CoachingSnapshot
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
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import (
    CandidateProfileSnapshot,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot import (
    KnowledgeSnapshot,
    PolicyVersions,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot_builder import (
    KnowledgeSnapshotBuilder,
)
from domain.contracts.narrative.narrative import Narrative
from domain.contracts.narrative.narrative_builder import NarrativeBuilder
from domain.contracts.narrative.narrative_section import NarrativeSection
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CANDIDATE_ID = "cand-test-001"
SESSION_ID = "sess-test-001"
SNAPSHOT_ID = "snap-test-001"
FIXED_DT = datetime(2026, 7, 2, 1, 0, 0, tzinfo=timezone.utc)

REASONING_IDENTITY = FeatureIdentity.for_type(FeatureType.REASONING)


# ---------------------------------------------------------------------------
# ProfileFeature helpers
# ---------------------------------------------------------------------------

def make_profile_feature(
    candidate_id: str = CANDIDATE_ID,
    feature_type: FeatureType = FeatureType.REASONING,
    confidence: float = 0.75,
    question_index: int = 3,
) -> ProfileFeature:
    identity = FeatureIdentity.for_type(feature_type)
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
            computed_at_question_index=question_index,
            feature_engine_version="1.0",
            updater_id="updater-reasoning",
        ),
        computed_at_question_index=question_index,
        candidate_identity_id=candidate_id,
    )


# ---------------------------------------------------------------------------
# CandidateProfileSnapshot helpers
# ---------------------------------------------------------------------------

def make_candidate_profile_snapshot(
    candidate_id: str = CANDIDATE_ID,
    features: tuple[ProfileFeature, ...] | None = None,
) -> CandidateProfileSnapshot:
    resolved = features if features is not None else (make_profile_feature(candidate_id=candidate_id),)
    return CandidateProfileSnapshot(
        candidate_identity_id=candidate_id,
        features=resolved,
        closed_at_question_index=5,
        source_observation_ids=("obs-1", "obs-2"),
        total_feature_count=len(resolved),
        mean_confidence=sum(f.quality.confidence.value for f in resolved) / len(resolved) if resolved else 0.0,
    )


# ---------------------------------------------------------------------------
# Narrative helpers (reuse NarrativeBuilder)
# ---------------------------------------------------------------------------

def make_section(section_type: NarrativeSectionType) -> NarrativeSection:
    return NarrativeSection(
        section_type=section_type,
        prose="Test prose.",
        feature_references=(REASONING_IDENTITY,),
        confidence_context="High confidence.",
    )


def make_narrative() -> Narrative:
    return (
        NarrativeBuilder()
        .with_executive_summary(make_section(NarrativeSectionType.EXECUTIVE_SUMMARY))
        .with_strengths(make_section(NarrativeSectionType.STRENGTHS))
        .with_weaknesses(make_section(NarrativeSectionType.WEAKNESSES))
        .with_growth_areas(make_section(NarrativeSectionType.GROWTH))
        .with_recommendations(make_section(NarrativeSectionType.RECOMMENDATIONS))
        .build()
    )


# ---------------------------------------------------------------------------
# PolicyVersions helpers
# ---------------------------------------------------------------------------

def make_policy_versions() -> PolicyVersions:
    return PolicyVersions(
        feature_engine_version="1.0",
        language_policy_version="1.0",
        ttl_policy_version="1.0",
        evaluation_policy_version="1.0",
        narrative_schema_version="1.0",
        coaching_schema_version="1.0",
        profile_schema_version="1.0",
    )


# ---------------------------------------------------------------------------
# CoachingSnapshot helpers
# ---------------------------------------------------------------------------

def make_coaching_snapshot(session_id: str = SESSION_ID) -> CoachingSnapshot:
    return CoachingBuilder.empty(session_id=session_id, question_index=5)


# ---------------------------------------------------------------------------
# KnowledgeSnapshot helpers
# ---------------------------------------------------------------------------

def make_knowledge_snapshot(
    session_id: str = SESSION_ID,
    candidate_id: str = CANDIDATE_ID,
) -> KnowledgeSnapshot:
    profile_snapshot = make_candidate_profile_snapshot(candidate_id=candidate_id)
    return (
        KnowledgeSnapshotBuilder()
        .with_session_id(session_id)
        .with_candidate_identity_id(candidate_id)
        .with_profile_snapshot(profile_snapshot)
        .with_narrative(make_narrative())
        .with_coaching_snapshot(make_coaching_snapshot(session_id=session_id))
        .with_policy_versions(make_policy_versions())
        .with_snapshot_id(SNAPSHOT_ID)
        .with_created_at(FIXED_DT)
        .build()
    )


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def candidate_id() -> str:
    return CANDIDATE_ID


@pytest.fixture
def session_id() -> str:
    return SESSION_ID


@pytest.fixture
def policy_versions() -> PolicyVersions:
    return make_policy_versions()


@pytest.fixture
def profile_snapshot() -> CandidateProfileSnapshot:
    return make_candidate_profile_snapshot()


@pytest.fixture
def narrative() -> Narrative:
    return make_narrative()


@pytest.fixture
def coaching_snapshot() -> CoachingSnapshot:
    return make_coaching_snapshot()


@pytest.fixture
def knowledge_snapshot() -> KnowledgeSnapshot:
    return make_knowledge_snapshot()
