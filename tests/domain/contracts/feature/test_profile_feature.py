# tests/domain/contracts/feature/test_profile_feature.py

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


def _make_quality(
    confidence: float = 0.8,
    stability: str = "stable",
    obs_count: int = 4,
) -> FeatureQuality:
    return FeatureQuality(
        confidence=FeatureConfidence(value=confidence),
        stability=FeatureStability(state=stability),
        maturity=FeatureMaturity.from_observation_count(obs_count),
    )


def _make_provenance(
    feature_type: FeatureType = FeatureType.REASONING,
    question_index: int = 3,
    obs_ids: tuple[str, ...] = ("obs-1",),
) -> FeatureProvenance:
    return FeatureProvenance(
        feature_identity=FeatureIdentity.for_type(feature_type),
        source_observation_ids=obs_ids,
        computed_at_question_index=question_index,
        feature_engine_version="1.0.0",
        updater_id="observation_updater",
    )


def _make_profile_feature(
    feature_type: FeatureType = FeatureType.REASONING,
    value: str = "HIGH",
    candidate_identity_id: str = "candidate-001",
    question_index: int = 3,
    schema_version: str = "1.0",
) -> ProfileFeature:
    return ProfileFeature(
        feature_identity=FeatureIdentity.for_type(feature_type),
        value=value,
        quality=_make_quality(),
        provenance=_make_provenance(feature_type=feature_type, question_index=question_index),
        computed_at_question_index=question_index,
        candidate_identity_id=candidate_identity_id,
        schema_version=schema_version,
    )


class TestProfileFeatureConstruction:
    def test_valid_minimal(self) -> None:
        pf = _make_profile_feature()
        assert pf.value == "HIGH"
        assert pf.candidate_identity_id == "candidate-001"
        assert pf.computed_at_question_index == 3

    def test_default_schema_version(self) -> None:
        pf = _make_profile_feature()
        assert pf.schema_version == "1.0"

    def test_custom_schema_version(self) -> None:
        pf = _make_profile_feature(schema_version="2.0")
        assert pf.schema_version == "2.0"

    def test_empty_value_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProfileFeature(
                feature_identity=FeatureIdentity.for_type(FeatureType.REASONING),
                value="",
                quality=_make_quality(),
                provenance=_make_provenance(),
                computed_at_question_index=3,
                candidate_identity_id="c-001",
            )

    def test_empty_candidate_identity_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProfileFeature(
                feature_identity=FeatureIdentity.for_type(FeatureType.REASONING),
                value="HIGH",
                quality=_make_quality(),
                provenance=_make_provenance(),
                computed_at_question_index=3,
                candidate_identity_id="",
            )

    def test_negative_question_index_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProfileFeature(
                feature_identity=FeatureIdentity.for_type(FeatureType.REASONING),
                value="HIGH",
                quality=_make_quality(),
                provenance=_make_provenance(),
                computed_at_question_index=-1,
                candidate_identity_id="c-001",
            )

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ProfileFeature(
                feature_identity=FeatureIdentity.for_type(FeatureType.REASONING),
                value="HIGH",
                quality=_make_quality(),
                provenance=_make_provenance(),
                computed_at_question_index=3,
                candidate_identity_id="c-001",
                unknown_field="x",
            )

    def test_immutability(self) -> None:
        pf = _make_profile_feature()
        with pytest.raises(ValidationError):
            pf.value = "LOW"  # type: ignore[misc]

    def test_equality(self) -> None:
        a = _make_profile_feature()
        b = _make_profile_feature()
        assert a == b

    def test_inequality_different_value(self) -> None:
        a = _make_profile_feature(value="HIGH")
        b = _make_profile_feature(value="LOW")
        assert a != b

    def test_inequality_different_candidate(self) -> None:
        a = _make_profile_feature(candidate_identity_id="c-001")
        b = _make_profile_feature(candidate_identity_id="c-002")
        assert a != b


class TestProfileFeatureAllTypes:
    @pytest.mark.parametrize("ft", list(FeatureType))
    def test_profile_feature_for_every_type(self, ft: FeatureType) -> None:
        pf = _make_profile_feature(feature_type=ft)
        assert pf.feature_identity.feature_type_id == ft.value


class TestProfileFeatureLanguageInvariant:
    """ADR-018 §C: feature type ID must never reference a programming language."""

    def test_no_language_in_any_feature_type_id(self) -> None:
        forbidden = {"python", "java", "javascript", "typescript", "go", "rust"}
        for ft in FeatureType:
            pf = _make_profile_feature(feature_type=ft)
            for lang in forbidden:
                assert lang not in pf.feature_identity.feature_type_id.lower()

    def test_language_capability_type_id_is_still_generic(self) -> None:
        pf = _make_profile_feature(feature_type=FeatureType.LANGUAGE_CAPABILITY)
        assert pf.feature_identity.feature_type_id == "language_capability_feature"

    def test_language_context_only_in_provenance(self) -> None:
        """Language context must live in provenance.language_context, not in the feature itself."""
        prov = FeatureProvenance(
            feature_identity=FeatureIdentity.for_type(FeatureType.LANGUAGE_CAPABILITY),
            source_observation_ids=("obs-1",),
            computed_at_question_index=2,
            feature_engine_version="1.0.0",
            updater_id="observation_updater",
            language_context="python",
        )
        pf = ProfileFeature(
            feature_identity=FeatureIdentity.for_type(FeatureType.LANGUAGE_CAPABILITY),
            value="HIGH",
            quality=_make_quality(),
            provenance=prov,
            computed_at_question_index=2,
            candidate_identity_id="c-001",
        )
        assert pf.provenance.language_context == "python"
        assert "python" not in pf.feature_identity.feature_type_id


class TestProfileFeatureVersioning:
    """ADR-018 §G: schema_version travels with every ProfileFeature."""

    def test_schema_version_present(self) -> None:
        pf = _make_profile_feature()
        assert pf.schema_version is not None

    def test_schema_version_minor_bump(self) -> None:
        pf = _make_profile_feature(schema_version="1.1")
        assert pf.schema_version == "1.1"

    def test_schema_version_major_bump(self) -> None:
        pf = _make_profile_feature(schema_version="2.0")
        assert pf.schema_version == "2.0"

    def test_two_features_different_schema_versions_are_not_equal(self) -> None:
        a = _make_profile_feature(schema_version="1.0")
        b = _make_profile_feature(schema_version="2.0")
        assert a != b
