# tests/domain/contracts/feature/test_feature_layer_invariants.py
# ADR-018 and ADR-020 architectural invariants

import pytest

from domain.contracts.feature import (
    FeatureCandidate,
    FeatureComposer,
    FeatureConfidence,
    FeatureIdentity,
    FeatureMergePolicy,
    FeatureMaturity,
    FeatureProvenance,
    FeatureQuality,
    FeatureReplacementPolicy,
    FeatureStability,
    FeatureType,
    FeatureUpdater,
    ProfileFeature,
)


class TestADR018Invariants:
    """ADR-018 architectural invariants verified at the contract layer."""

    def test_eleven_v12_feature_types(self) -> None:
        """ADR-018 §D: exactly 11 V1.2 feature types."""
        assert len(list(FeatureType)) == 11

    def test_no_language_reference_in_type_ids(self) -> None:
        """ADR-018 §C: no type name may reference a programming language."""
        forbidden = {"python", "java", "javascript", "typescript", "go", "rust", "csharp", "kotlin"}
        for ft in FeatureType:
            for lang in forbidden:
                assert lang not in ft.value.lower(), (
                    f"Feature type '{ft.value}' references language '{lang}'"
                )

    def test_profile_feature_carries_schema_version(self) -> None:
        """ADR-018 §G: schema_version must travel with the ProfileFeature."""
        pf = _build_profile_feature(FeatureType.REASONING)
        assert pf.schema_version is not None
        assert len(pf.schema_version) > 0

    def test_profile_feature_immutable_per_cycle(self) -> None:
        """ADR-018 §C: ProfileFeature is immutable per computation cycle."""
        from pydantic import ValidationError
        pf = _build_profile_feature(FeatureType.COMMUNICATION)
        with pytest.raises(ValidationError):
            pf.value = "CHANGED"  # type: ignore[misc]

    def test_feature_candidate_identity_id_non_empty(self) -> None:
        """ADR-018 §C: candidate_identity_id is required (ADR-016A)."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            _build_profile_feature(FeatureType.REASONING, candidate_identity_id="")

    def test_provenance_observation_ids_required(self) -> None:
        """ADR-018 §F: every ProfileFeature must be traceable to source Observations."""
        pf = _build_profile_feature(FeatureType.TECHNICAL_SKILL)
        assert isinstance(pf.provenance.source_observation_ids, tuple)

    def test_confidence_in_valid_range(self) -> None:
        """ADR-018 §J: confidence in [0.0, 1.0]."""
        pf = _build_profile_feature(FeatureType.TREND)
        assert 0.0 <= pf.quality.confidence.value <= 1.0

    def test_stability_is_one_of_three_states(self) -> None:
        """ADR-018 §J: stability in {stable, unstable, emerging}."""
        valid = {"stable", "unstable", "emerging"}
        for ft in FeatureType:
            pf = _build_profile_feature(ft)
            assert pf.quality.stability.state in valid

    def test_maturity_is_one_of_three_stages(self) -> None:
        """ADR-018 §J: maturity in {nascent, developing, mature}."""
        valid = {"nascent", "developing", "mature"}
        for ft in FeatureType:
            pf = _build_profile_feature(ft)
            assert pf.quality.maturity.stage in valid

    def test_language_capability_allows_language_context_in_provenance(self) -> None:
        """ADR-018 §D: LanguageCapabilityFeature is the sole exception for language_context."""
        prov = FeatureProvenance(
            feature_identity=FeatureIdentity.for_type(FeatureType.LANGUAGE_CAPABILITY),
            source_observation_ids=("obs-1",),
            computed_at_question_index=3,
            feature_engine_version="1.0.0",
            updater_id="observation_updater",
            language_context="python",
        )
        assert prov.language_context == "python"

    def test_non_capability_features_should_have_no_language_context(self) -> None:
        """ADR-018 §D: all other types are fully language-independent."""
        for ft in FeatureType:
            if ft is FeatureType.LANGUAGE_CAPABILITY:
                continue
            pf = _build_profile_feature(ft)
            assert pf.provenance.language_context is None


class TestADR020Invariants:
    """ADR-020 architectural invariants verified at the contract layer."""

    def test_feature_identity_stable_across_schema_versions(self) -> None:
        """ADR-020 §F: schema evolution must never change FeatureIdentity."""
        fi_v1 = FeatureIdentity(
            feature_type_id="reasoning_feature",
            semantic_category="analytical_reasoning",
            schema_version="1.0",
        )
        fi_v2 = FeatureIdentity(
            feature_type_id="reasoning_feature",
            semantic_category="analytical_reasoning",
            schema_version="2.0",
        )
        assert fi_v1.feature_type_id == fi_v2.feature_type_id
        assert fi_v1.semantic_category == fi_v2.semantic_category

    def test_feature_candidate_requires_non_empty_source_ids(self) -> None:
        """ADR-020 §E: every FeatureCandidate must be traceable."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            FeatureCandidate(
                feature_identity=FeatureIdentity.for_type(FeatureType.REASONING),
                candidate_value="HIGH",
                candidate_confidence=0.8,
                source_observation_ids=(),
                computed_at_question_index=3,
                updater_id="test_updater",
            )

    def test_feature_candidate_immutable(self) -> None:
        """ADR-020 §C: candidates are immutable value objects."""
        from pydantic import ValidationError
        fc = FeatureCandidate(
            feature_identity=FeatureIdentity.for_type(FeatureType.REASONING),
            candidate_value="HIGH",
            candidate_confidence=0.8,
            source_observation_ids=("obs-1",),
            computed_at_question_index=3,
            updater_id="test_updater",
        )
        with pytest.raises(ValidationError):
            fc.candidate_value = "LOW"  # type: ignore[misc]

    def test_composer_is_abstract(self) -> None:
        """ADR-020 §C: FeatureComposer must be subclassed; cannot be instantiated."""
        with pytest.raises(TypeError):
            FeatureComposer()  # type: ignore[abstract]

    def test_updater_is_abstract(self) -> None:
        """ADR-020 §C: FeatureUpdater must be subclassed; cannot be instantiated."""
        with pytest.raises(TypeError):
            FeatureUpdater()  # type: ignore[abstract]

    def test_merge_policy_is_abstract(self) -> None:
        """ADR-020 §C: FeatureMergePolicy must be subclassed."""
        with pytest.raises(TypeError):
            FeatureMergePolicy()  # type: ignore[abstract]

    def test_replacement_policy_is_abstract(self) -> None:
        """ADR-020 §C: FeatureReplacementPolicy must be subclassed."""
        with pytest.raises(TypeError):
            FeatureReplacementPolicy()  # type: ignore[abstract]

    def test_extra_fields_forbidden_on_all_contracts(self) -> None:
        """All contracts use extra='forbid' to prevent silent misuse."""
        from pydantic import ValidationError
        contracts_to_test = [
            lambda: FeatureIdentity(
                feature_type_id="t", semantic_category="c", extra_field="x"  # type: ignore
            ),
            lambda: FeatureConfidence(value=0.5, extra_field="x"),  # type: ignore
            lambda: FeatureStability(state="stable", extra_field="x"),  # type: ignore
            lambda: FeatureMaturity(stage="nascent", observation_count=1, extra_field="x"),  # type: ignore
        ]
        for factory in contracts_to_test:
            with pytest.raises(ValidationError):
                factory()

    def test_provenance_carries_feature_engine_version(self) -> None:
        """ADR-020 §G: feature_engine_version is required in provenance."""
        prov = FeatureProvenance(
            feature_identity=FeatureIdentity.for_type(FeatureType.REASONING),
            source_observation_ids=("obs-1",),
            computed_at_question_index=3,
            feature_engine_version="1.2.0",
            updater_id="observation_updater",
        )
        assert prov.feature_engine_version == "1.2.0"

    def test_provenance_carries_updater_id(self) -> None:
        """ADR-020 §G: updater_id is required in provenance."""
        prov = FeatureProvenance(
            feature_identity=FeatureIdentity.for_type(FeatureType.REASONING),
            source_observation_ids=("obs-1",),
            computed_at_question_index=3,
            feature_engine_version="1.0.0",
            updater_id="observation_updater",
        )
        assert prov.updater_id == "observation_updater"

    def test_provenance_superseded_ids_default_empty(self) -> None:
        """ADR-020 §I: discarded candidates' provenance captured; default empty."""
        prov = FeatureProvenance(
            feature_identity=FeatureIdentity.for_type(FeatureType.REASONING),
            source_observation_ids=("obs-1",),
            computed_at_question_index=3,
            feature_engine_version="1.0.0",
            updater_id="observation_updater",
        )
        assert prov.superseded_observation_ids == ()


class TestPackagePublicAPI:
    """Verify __init__.py exports all required public symbols."""

    def test_all_required_symbols_exported(self) -> None:
        import domain.contracts.feature as pkg
        required = [
            "FeatureType",
            "FeatureIdentity",
            "FeatureConfidence",
            "FeatureStability",
            "FeatureMaturity",
            "FeatureQuality",
            "FeatureProvenance",
            "FeatureCandidate",
            "ProfileFeature",
            "FeatureComposer",
            "FeatureUpdater",
            "FeatureMergePolicy",
            "FeatureReplacementPolicy",
        ]
        for symbol in required:
            assert hasattr(pkg, symbol), f"Missing public symbol: {symbol}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_profile_feature(
    feature_type: FeatureType,
    candidate_identity_id: str = "candidate-001",
    confidence: float = 0.8,
    stability: str = "stable",
    obs_count: int = 4,
) -> ProfileFeature:
    identity = FeatureIdentity.for_type(feature_type)
    prov = FeatureProvenance(
        feature_identity=identity,
        source_observation_ids=("obs-1",),
        computed_at_question_index=3,
        feature_engine_version="1.0.0",
        updater_id="observation_updater",
    )
    quality = FeatureQuality(
        confidence=FeatureConfidence(value=confidence),
        stability=FeatureStability(state=stability),
        maturity=FeatureMaturity.from_observation_count(obs_count),
    )
    return ProfileFeature(
        feature_identity=identity,
        value="HIGH",
        quality=quality,
        provenance=prov,
        computed_at_question_index=3,
        candidate_identity_id=candidate_identity_id,
    )
