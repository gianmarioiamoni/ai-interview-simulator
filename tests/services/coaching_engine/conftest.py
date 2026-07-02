# tests/services/coaching_engine/conftest.py
# Shared fixtures for CoachingEngine test suite (E04-M1)

from __future__ import annotations

import pytest

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.feature.feature_quality import (
    FeatureConfidence,
    FeatureMaturity,
    FeatureQuality,
    FeatureStability,
    MATURITY_DEVELOPING,
    STABILITY_STABLE,
)
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.language.language_profile import LanguageProfile, SessionMode
from domain.contracts.language.programming_language import ProgrammingLanguage
from domain.contracts.language.language_selection_strategy import LanguageSelectionStrategy
from domain.contracts.reasoning.candidate_profile import CandidateProfile
from services.coaching_engine.coaching_context import CoachingContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_feature(
    feature_type: FeatureType,
    value: str,
    confidence: float = 0.8,
    question_index: int = 2,
    candidate_id: str = "cand-001",
) -> ProfileFeature:
    identity = FeatureIdentity.for_type(feature_type)
    return ProfileFeature(
        feature_identity=identity,
        value=value,
        quality=FeatureQuality(
            confidence=FeatureConfidence(value=confidence),
            stability=FeatureStability(state=STABILITY_STABLE),
            maturity=FeatureMaturity(stage=MATURITY_DEVELOPING, observation_count=3),
        ),
        provenance=FeatureProvenance(
            feature_identity=identity,
            source_observation_ids=("obs-1",),
            computed_at_question_index=question_index,
            feature_engine_version="1.0.0",
            updater_id="technical_skill_feature_updater",
        ),
        computed_at_question_index=question_index,
        candidate_identity_id=candidate_id,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def candidate_profile() -> CandidateProfile:
    return CandidateProfile(
        questions_answered=3,
        areas_covered=["algorithms", "system design"],
        last_updated_at_question_index=2,
    )


@pytest.fixture
def weak_technical_feature() -> ProfileFeature:
    return make_feature(FeatureType.TECHNICAL_SKILL, "LOW", confidence=0.75)


@pytest.fixture
def strong_reasoning_feature() -> ProfileFeature:
    return make_feature(FeatureType.REASONING, "HIGH", confidence=0.85)


@pytest.fixture
def weak_reasoning_feature() -> ProfileFeature:
    return make_feature(FeatureType.REASONING, "LOW", confidence=0.6)


@pytest.fixture
def weak_coverage_feature() -> ProfileFeature:
    return make_feature(FeatureType.COVERAGE, "LOW", confidence=0.5)


@pytest.fixture
def mixed_features(
    weak_technical_feature: ProfileFeature,
    strong_reasoning_feature: ProfileFeature,
    weak_coverage_feature: ProfileFeature,
) -> tuple[ProfileFeature, ...]:
    return (weak_technical_feature, strong_reasoning_feature, weak_coverage_feature)


@pytest.fixture
def base_context(
    candidate_profile: CandidateProfile,
    mixed_features: tuple[ProfileFeature, ...],
) -> CoachingContext:
    return CoachingContext(
        session_id="session-001",
        candidate_identity_id="cand-001",
        question_index=2,
        profile=candidate_profile,
        features=mixed_features,
        knowledge_gap_observation_ids=("obs-gap-1",),
        interview_topic="System Design",
        interview_role="Senior Engineer",
    )


@pytest.fixture
def empty_context(candidate_profile: CandidateProfile) -> CoachingContext:
    return CoachingContext(
        session_id="session-empty",
        candidate_identity_id="cand-001",
        question_index=0,
        profile=candidate_profile,
        features=(),
        knowledge_gap_observation_ids=(),
    )
