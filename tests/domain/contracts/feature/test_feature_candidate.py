# tests/domain/contracts/feature/test_feature_candidate.py

import pytest
from pydantic import ValidationError

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_type import FeatureType


def _make_candidate(**kwargs) -> FeatureCandidate:
    defaults = dict(
        feature_identity=FeatureIdentity.for_type(FeatureType.REASONING),
        candidate_value="HIGH",
        candidate_confidence=0.8,
        source_observation_ids=("obs-1",),
        computed_at_question_index=5,
        updater_id="observation_updater",
    )
    defaults.update(kwargs)
    return FeatureCandidate(**defaults)


class TestFeatureCandidateConstruction:
    def test_valid_minimal(self) -> None:
        fc = _make_candidate()
        assert fc.candidate_value == "HIGH"
        assert fc.candidate_confidence == 0.8
        assert fc.computed_at_question_index == 5

    def test_default_schema_version(self) -> None:
        assert _make_candidate().schema_version == "1.0"

    def test_default_language_context_none(self) -> None:
        assert _make_candidate().language_context is None

    def test_language_context_set(self) -> None:
        fc = _make_candidate(language_context="python")
        assert fc.language_context == "python"

    def test_confidence_boundary_zero(self) -> None:
        fc = _make_candidate(candidate_confidence=0.0)
        assert fc.candidate_confidence == 0.0

    def test_confidence_boundary_one(self) -> None:
        fc = _make_candidate(candidate_confidence=1.0)
        assert fc.candidate_confidence == 1.0

    def test_confidence_below_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_candidate(candidate_confidence=-0.01)

    def test_confidence_above_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_candidate(candidate_confidence=1.01)

    def test_empty_value_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_candidate(candidate_value="")

    def test_empty_updater_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_candidate(updater_id="")

    def test_empty_source_observation_ids_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_candidate(source_observation_ids=())

    def test_negative_question_index_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_candidate(computed_at_question_index=-1)

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            _make_candidate(unknown="x")

    def test_immutability(self) -> None:
        fc = _make_candidate()
        with pytest.raises(ValidationError):
            fc.candidate_value = "LOW"  # type: ignore[misc]

    def test_source_ids_preserved(self) -> None:
        fc = _make_candidate(source_observation_ids=("obs-a", "obs-b"))
        assert fc.source_observation_ids == ("obs-a", "obs-b")

    def test_equality(self) -> None:
        a = _make_candidate()
        b = _make_candidate()
        assert a == b

    def test_inequality_different_value(self) -> None:
        a = _make_candidate(candidate_value="HIGH")
        b = _make_candidate(candidate_value="LOW")
        assert a != b

    def test_feature_identity_carried(self) -> None:
        fc = _make_candidate()
        assert fc.feature_identity.feature_type_id == "reasoning_feature"


class TestFeatureCandidateAllTypes:
    @pytest.mark.parametrize("ft", list(FeatureType))
    def test_candidate_for_every_feature_type(self, ft: FeatureType) -> None:
        fc = _make_candidate(feature_identity=FeatureIdentity.for_type(ft))
        assert fc.feature_identity.feature_type_id == ft.value
