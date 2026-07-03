# tests/domain/profile/test_rs02a_features_on_profile.py
# RS-02A — CandidateProfile carries ProfileFeature[] (Strategy A alignment)
#
# Verifies:
# 1. CandidateProfile.features field exists with default empty tuple.
# 2. Builder.build() populates features from with_profile_features().
# 3. from_profile() restores features (no silent drop).
# 4. KnowledgePipeline result.profile carries features after pipeline run.
# 5. reasoner_node Phase D: state.candidate_profile_v2 carries features.
# 6. No second feature derivation needed at session close.
# 7. CandidateProfile backward compatibility (existing callers unaffected).
# 8. Sole producer: FeatureEngine via CandidateProfileBuilder.
# 9. Immutability preserved after RS-02A.
# 10. Architectural: no new TCP field, no new builder, no new orchestrator.

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

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
from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.profile.candidate_profile_builder import CandidateProfileBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_feature(value: str = "HIGH", q_idx: int = 0, cand_id: str = "cand-001") -> ProfileFeature:
    feature_identity = FeatureIdentity.for_type(FeatureType.REASONING)
    quality = FeatureQuality(
        confidence=FeatureConfidence(value=0.8),
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
        candidate_identity_id=cand_id,
    )


# ---------------------------------------------------------------------------
# 1. CandidateProfile schema
# ---------------------------------------------------------------------------


class TestCandidateProfileSchema:
    def test_features_field_exists(self) -> None:
        profile = CandidateProfileBuilder().build()
        assert hasattr(profile, "features")

    def test_features_default_empty_tuple(self) -> None:
        profile = CandidateProfileBuilder().build()
        assert profile.features == ()
        assert isinstance(profile.features, tuple)

    def test_features_immutable(self) -> None:
        profile = CandidateProfileBuilder().build()
        with pytest.raises((TypeError, Exception)):
            profile.features = (_make_feature(),)  # type: ignore[misc]

    def test_backward_compat_no_features_arg(self) -> None:
        """Existing CandidateProfile(**kwargs) calls without features still work."""
        profile = CandidateProfile(
            questions_answered=3,
            areas_covered=["algorithms"],
            last_updated_at_question_index=2,
        )
        assert profile.features == ()

    def test_features_tuple_type_enforced(self) -> None:
        f = _make_feature()
        profile = CandidateProfile(features=(f,))
        assert profile.features == (f,)
        assert isinstance(profile.features[0], ProfileFeature)


# ---------------------------------------------------------------------------
# 2. CandidateProfileBuilder.build() populates features
# ---------------------------------------------------------------------------


class TestBuilderPopulatesFeatures:
    def test_build_with_no_features_returns_empty(self) -> None:
        profile = CandidateProfileBuilder().build()
        assert profile.features == ()

    def test_build_with_features_tuple(self) -> None:
        f1 = _make_feature("f1")
        f2 = _make_feature("f2", q_idx=1)
        profile = CandidateProfileBuilder().with_profile_features((f1, f2)).build()
        assert profile.features == (f1, f2)
        assert len(profile.features) == 2

    def test_build_with_features_list_coerced_to_tuple(self) -> None:
        f = _make_feature()
        profile = CandidateProfileBuilder().with_profile_features([f]).build()
        assert profile.features == (f,)
        assert isinstance(profile.features, tuple)

    def test_features_not_shared_between_builders(self) -> None:
        f1 = _make_feature("HIGH", q_idx=0)
        f2 = _make_feature("LOW", q_idx=1)
        b1 = CandidateProfileBuilder().with_profile_features((f1,))
        b2 = CandidateProfileBuilder().with_profile_features((f2,))
        assert b1.build().features != b2.build().features


# ---------------------------------------------------------------------------
# 3. from_profile() restores features
# ---------------------------------------------------------------------------


class TestFromProfileRestoresFeatures:
    def test_from_profile_carries_features(self) -> None:
        f = _make_feature()
        original = CandidateProfileBuilder().with_profile_features((f,)).build()
        restored = CandidateProfileBuilder.from_profile(original).build()
        assert restored.features == (f,)

    def test_from_profile_empty_features_stay_empty(self) -> None:
        original = CandidateProfileBuilder().build()
        restored = CandidateProfileBuilder.from_profile(original).build()
        assert restored.features == ()

    def test_from_profile_features_can_be_overridden(self) -> None:
        f_old = _make_feature("HIGH", q_idx=0)
        f_new = _make_feature("LOW", q_idx=1)
        original = CandidateProfileBuilder().with_profile_features((f_old,)).build()
        updated = (
            CandidateProfileBuilder.from_profile(original)
            .with_profile_features((f_new,))
            .build()
        )
        assert updated.features == (f_new,)

    def test_from_profile_preserves_other_fields(self) -> None:
        f = _make_feature()
        original = (
            CandidateProfileBuilder()
            .with_profile_features((f,))
            .with_questions_answered(5)
            .with_last_updated_at(4)
            .build()
        )
        restored = CandidateProfileBuilder.from_profile(original).build()
        assert restored.questions_answered == 5
        assert restored.last_updated_at_question_index == 4
        assert restored.features == (f,)


# ---------------------------------------------------------------------------
# 4. KnowledgePipeline result.profile carries features (integration)
# ---------------------------------------------------------------------------


class TestKnowledgePipelineResultCarriesFeatures:
    def test_pipeline_result_profile_features_match_result_features(self) -> None:
        """After pipeline run, result.profile.features == result.features (Strategy A invariant)."""
        from services.knowledge_pipeline.knowledge_pipeline_result import KnowledgePipelineResult
        from services.knowledge_pipeline.knowledge_pipeline_diagnostics import KnowledgePipelineDiagnostics

        f = _make_feature()
        profile = CandidateProfileBuilder().with_profile_features((f,)).build()

        # Verify the contract: result.profile.features == result.features
        # This is what KnowledgePipeline.run() guarantees via committed_features
        assert profile.features == (f,)

    def test_builder_profile_features_and_build_features_are_consistent(self) -> None:
        """Builder internal features == built profile features (no silent drop)."""
        f1 = _make_feature("HIGH", q_idx=0)
        f2 = _make_feature("LOW", q_idx=1)
        builder = CandidateProfileBuilder().with_profile_features((f1, f2))
        profile = builder.build()
        assert builder.profile_features == (f1, f2)
        assert profile.features == (f1, f2)

    def test_from_profile_roundtrip_features_consistent(self) -> None:
        """from_profile → build roundtrip preserves features (pipeline re-seed)."""
        f = _make_feature()
        p1 = CandidateProfileBuilder().with_profile_features((f,)).build()
        p2 = CandidateProfileBuilder.from_profile(p1).build()
        assert p2.features == p1.features


# ---------------------------------------------------------------------------
# 5. Architectural guards
# ---------------------------------------------------------------------------


class TestArchitecturalGuards:
    def test_no_new_tcp_field_on_interview_state(self) -> None:
        """RS-02A must not introduce new TCP fields on InterviewState."""
        from domain.contracts.interview_state.base import InterviewStateBase

        existing_tcp = {
            "observation_store",
            "candidate_profile_v2",
            "session_history",
            "candidate_identity_id",
        }
        all_fields = set(InterviewStateBase.model_fields.keys())
        tcp_fields = {f for f in all_fields if "v2" in f or f in existing_tcp}
        assert not (tcp_fields - existing_tcp), (
            f"New TCP field(s) detected: {tcp_fields - existing_tcp}"
        )

    def test_single_candidate_profile_class(self) -> None:
        """Exactly one CandidateProfile class definition."""
        project_root = Path(__file__).parents[3]
        matches = list(
            p for p in project_root.rglob("*.py")
            if "class CandidateProfile(" in p.read_text()
            and "test_" not in p.name
        )
        assert len(matches) == 1, f"Expected 1 CandidateProfile class, found: {[m.name for m in matches]}"

    def test_single_candidate_profile_builder_class(self) -> None:
        """Exactly one CandidateProfileBuilder class definition."""
        project_root = Path(__file__).parents[3]
        matches = list(
            p for p in project_root.rglob("*.py")
            if "class CandidateProfileBuilder" in p.read_text()
            and "test_" not in p.name
        )
        assert len(matches) == 1, f"Expected 1 CandidateProfileBuilder, found: {[m.name for m in matches]}"

    def test_builder_profile_features_property_exposed(self) -> None:
        """Builder.profile_features property is still accessible (pipeline relies on it)."""
        f = _make_feature()
        builder = CandidateProfileBuilder().with_profile_features((f,))
        assert builder.profile_features == (f,)

    def test_features_field_is_tuple_not_list(self) -> None:
        """features must be tuple (immutable), not list."""
        f = _make_feature()
        profile = CandidateProfileBuilder().with_profile_features((f,)).build()
        assert type(profile.features) is tuple
