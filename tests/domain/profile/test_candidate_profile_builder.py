# tests/domain/profile/test_candidate_profile_builder.py
"""Tests for CandidateProfileBuilder — contract, behavior, architecture."""

import pytest
from pydantic import ValidationError

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
from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.profile_signal import ProfileSignal
from domain.contracts.reasoning.signal_trace import SignalTrace
from domain.profile.candidate_profile_builder import CandidateProfileBuilder


def _make_feature(
    feature_type: FeatureType = FeatureType.TECHNICAL_SKILL,
    value: str = "HIGH",
    q_idx: int = 0,
) -> ProfileFeature:
    feature_identity = FeatureIdentity.for_type(feature_type)
    quality = FeatureQuality(
        confidence=FeatureConfidence(value=0.9),
        stability=FeatureStability(state="stable"),
        maturity=FeatureMaturity.from_observation_count(4),
    )
    provenance = FeatureProvenance(
        feature_identity=feature_identity,
        source_observation_ids=("obs-1",),
        computed_at_question_index=q_idx,
        feature_engine_version="1.0.0",
        updater_id="test_updater",
    )
    return ProfileFeature(
        feature_identity=feature_identity,
        value=value,
        quality=quality,
        provenance=provenance,
        computed_at_question_index=q_idx,
        candidate_identity_id="cand-001",
    )


class TestBuilderContract:
    def test_build_returns_candidate_profile(self) -> None:
        profile = CandidateProfileBuilder().build()
        assert isinstance(profile, CandidateProfile)

    def test_build_returns_frozen_object(self) -> None:
        profile = CandidateProfileBuilder().build()
        with pytest.raises((ValidationError, TypeError)):
            profile.questions_answered = 5  # type: ignore[misc]

    def test_empty_build_has_defaults(self) -> None:
        profile = CandidateProfileBuilder().build()
        assert profile.questions_answered == 0
        assert profile.areas_covered == []
        assert profile.dimension_scores == {}
        assert profile.signals == {}
        assert profile.last_updated_at_question_index == -1
        assert profile.features == ()

    def test_extra_fields_forbidden(self) -> None:
        """CandidateProfile model_config extra=forbid must hold."""
        with pytest.raises(ValidationError):
            CandidateProfile(unknown_field="x")  # type: ignore[call-arg]

    def test_dimension_scores_not_a_model_field(self) -> None:
        """TD-EP10-001 — dimension_scores is a derived projection, not a peer field."""
        assert "dimension_scores" not in CandidateProfile.model_fields
        assert "features" in CandidateProfile.model_fields


class TestBuilderBehavior:
    def test_with_profile_features_derives_dimension_scores(self) -> None:
        feature = _make_feature(FeatureType.TECHNICAL_SKILL, "HIGH")
        profile = CandidateProfileBuilder().with_profile_features((feature,)).build()
        assert feature in profile.features
        assert ProfileDimension.TECHNICAL_DEPTH in profile.dimension_scores
        assert profile.dimension_scores[ProfileDimension.TECHNICAL_DEPTH].evidence_count >= 1

    def test_with_questions_answered(self) -> None:
        profile = CandidateProfileBuilder().with_questions_answered(7).build()
        assert profile.questions_answered == 7

    def test_with_questions_answered_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            CandidateProfileBuilder().with_questions_answered(-1)

    def test_with_areas_covered(self) -> None:
        profile = CandidateProfileBuilder().with_areas_covered(["a", "b"]).build()
        assert profile.areas_covered == ["a", "b"]

    def test_with_last_updated_at(self) -> None:
        profile = CandidateProfileBuilder().with_last_updated_at(5).build()
        assert profile.last_updated_at_question_index == 5

    def test_fluent_chaining_returns_self(self) -> None:
        builder = CandidateProfileBuilder()
        result = builder.with_questions_answered(1).with_areas_covered(["x"]).with_last_updated_at(0)
        assert result is builder

    def test_with_signal(self) -> None:
        st = SignalTrace()
        profile = CandidateProfileBuilder().with_signal(ProfileSignal.CONFIDENCE, st).build()
        assert profile.signals[ProfileSignal.CONFIDENCE] == st

    def test_with_dimension_removed(self) -> None:
        assert not hasattr(CandidateProfileBuilder, "with_dimension")
        assert not hasattr(CandidateProfileBuilder, "with_dimensions")


class TestBuilderFromProfile:
    def test_from_profile_copies_all_fields(self) -> None:
        feature = _make_feature()
        original = (
            CandidateProfileBuilder()
            .with_profile_features((feature,))
            .with_questions_answered(3)
            .with_areas_covered(["algorithms"])
            .with_last_updated_at(2)
            .build()
        )
        rebuilt = CandidateProfileBuilder.from_profile(original).build()
        assert rebuilt.features == original.features
        assert rebuilt.questions_answered == original.questions_answered
        assert rebuilt.areas_covered == original.areas_covered
        assert rebuilt.dimension_scores == original.dimension_scores

    def test_from_profile_mutations_do_not_affect_original(self) -> None:
        original = CandidateProfileBuilder().with_questions_answered(3).build()
        builder = CandidateProfileBuilder.from_profile(original)
        builder.with_questions_answered(999)
        assert original.questions_answered != 999

    def test_from_profile_allows_feature_override(self) -> None:
        original = (
            CandidateProfileBuilder()
            .with_profile_features((_make_feature(FeatureType.TECHNICAL_SKILL, "LOW"),))
            .with_questions_answered(1)
            .build()
        )
        updated = (
            CandidateProfileBuilder.from_profile(original)
            .with_profile_features((_make_feature(FeatureType.TECHNICAL_SKILL, "HIGH"),))
            .build()
        )
        assert updated.features[0].value == "HIGH"
        assert updated.questions_answered == original.questions_answered


class TestBuilderArchitecture:
    def test_build_always_returns_new_instance(self) -> None:
        builder = CandidateProfileBuilder()
        p1 = builder.build()
        p2 = builder.build()
        assert p1 is not p2

    def test_multiple_builds_are_equal(self) -> None:
        builder = CandidateProfileBuilder().with_questions_answered(3)
        assert builder.build() == builder.build()
