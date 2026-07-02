# tests/services/narrative_generator/conftest.py
# Shared fixtures for NarrativeGenerator test suite

from __future__ import annotations

import uuid
from typing import Any

import pytest

from domain.contracts.feature.feature_collection import FeatureCollection
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
from domain.contracts.language.language_profile import LanguageProfile, SessionMode
from domain.contracts.language.language_selection_strategy import LanguageSelectionStrategy
from domain.contracts.language.programming_language import ProgrammingLanguage
from domain.contracts.reasoning.candidate_profile import CandidateProfile
from services.narrative_generator.narrative_generation_context import NarrativeGenerationContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_feature(
    feature_type: FeatureType = FeatureType.REASONING,
    value: str = "HIGH",
    confidence: float = 0.8,
    question_index: int = 3,
    candidate_identity_id: str = "cand-001",
) -> ProfileFeature:
    identity = FeatureIdentity.for_type(feature_type)
    provenance = FeatureProvenance(
        feature_identity=identity,
        source_observation_ids=(str(uuid.uuid4()),),
        computed_at_question_index=question_index,
        feature_engine_version="1.0",
        updater_id="stub-updater",
    )
    quality = FeatureQuality(
        confidence=FeatureConfidence(value=confidence),
        stability=FeatureStability(state="emerging"),
        maturity=FeatureMaturity.from_observation_count(2),
    )
    return ProfileFeature(
        feature_identity=identity,
        value=value,
        quality=quality,
        provenance=provenance,
        computed_at_question_index=question_index,
        candidate_identity_id=candidate_identity_id,
    )


def make_language_profile(session_id: str = "sess-001") -> LanguageProfile:
    python = ProgrammingLanguage(
        language_id="python",
        display_name="Python",
        language_version="3.12",
        language_family="python",
    )
    return LanguageProfile(
        session_id=session_id,
        session_mode=SessionMode.SINGLE,
        primary_language=python,
        active_languages=[python],
        selection_strategy=LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING,
        language_sequence=["python", "python", "python", "python"],
    )


def make_profile(
    questions_answered: int = 4,
    areas_covered: list[str] | None = None,
) -> CandidateProfile:
    return CandidateProfile(
        questions_answered=questions_answered,
        areas_covered=["algorithms", "data-structures"] if areas_covered is None else areas_covered,
        last_updated_at_question_index=questions_answered - 1,
    )


def make_feature_collection(
    features: list[ProfileFeature] | None = None,
) -> FeatureCollection:
    return FeatureCollection.from_iterable(features or [])


def make_context(
    session_id: str = "sess-001",
    candidate_identity_id: str = "cand-001",
    question_index: int = 3,
    features: FeatureCollection | None = None,
    profile: CandidateProfile | None = None,
    knowledge_gap_areas: tuple[str, ...] = ("recursion", "dynamic programming"),
    evaluation_summary: dict[str, str] | None = None,
    interview_metadata: dict[str, str] | None = None,
    language_profile: LanguageProfile | None = None,
) -> NarrativeGenerationContext:
    return NarrativeGenerationContext(
        session_id=session_id,
        candidate_identity_id=candidate_identity_id,
        question_index=question_index,
        profile=profile or make_profile(),
        features=features or make_feature_collection(),
        language_profile=language_profile,
        knowledge_gap_areas=knowledge_gap_areas,
        evaluation_summary=evaluation_summary or {"technical_depth": "HIGH"},
        interview_metadata=interview_metadata or {"topic": "algorithms", "level": "mid"},
    )


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def session_id() -> str:
    return "sess-001"


@pytest.fixture
def candidate_id() -> str:
    return "cand-001"


@pytest.fixture
def empty_context(session_id: str, candidate_id: str) -> NarrativeGenerationContext:
    return make_context(
        session_id=session_id,
        candidate_identity_id=candidate_id,
        features=make_feature_collection([]),
    )


@pytest.fixture
def rich_features() -> FeatureCollection:
    return make_feature_collection([
        make_feature(FeatureType.REASONING, "HIGH", confidence=0.85),
        make_feature(FeatureType.TECHNICAL_SKILL, "MODERATE", confidence=0.5),
        make_feature(FeatureType.CONFIDENCE, "LOW", confidence=0.25),
    ])


@pytest.fixture
def rich_context(session_id: str, candidate_id: str, rich_features: FeatureCollection) -> NarrativeGenerationContext:
    return make_context(
        session_id=session_id,
        candidate_identity_id=candidate_id,
        features=rich_features,
        profile=make_profile(questions_answered=4, areas_covered=["algorithms", "system-design"]),
        knowledge_gap_areas=("dynamic programming", "graph algorithms"),
        evaluation_summary={"technical_depth": "HIGH", "problem_solving": "MODERATE"},
    )
