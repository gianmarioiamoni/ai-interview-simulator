# tests/domain/contracts/feature/test_feature_provenance.py

import pytest
from pydantic import ValidationError

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.feature.feature_type import FeatureType


def _make_identity() -> FeatureIdentity:
    return FeatureIdentity.for_type(FeatureType.REASONING)


def _make_provenance(**kwargs) -> FeatureProvenance:
    defaults = dict(
        feature_identity=_make_identity(),
        source_observation_ids=("obs-1", "obs-2"),
        computed_at_question_index=3,
        feature_engine_version="1.0.0",
        updater_id="observation_updater",
    )
    defaults.update(kwargs)
    return FeatureProvenance(**defaults)


class TestFeatureProvenanceConstruction:
    def test_minimal_valid(self) -> None:
        fp = _make_provenance()
        assert fp.computed_at_question_index == 3
        assert fp.feature_engine_version == "1.0.0"
        assert fp.updater_id == "observation_updater"

    def test_default_schema_version(self) -> None:
        fp = _make_provenance()
        assert fp.schema_version == "1.0"

    def test_default_empty_superseded(self) -> None:
        fp = _make_provenance()
        assert fp.superseded_observation_ids == ()

    def test_default_language_context_none(self) -> None:
        fp = _make_provenance()
        assert fp.language_context is None

    def test_language_context_set_for_capability_feature(self) -> None:
        fp = _make_provenance(language_context="python")
        assert fp.language_context == "python"

    def test_superseded_ids_stored(self) -> None:
        fp = _make_provenance(superseded_observation_ids=("obs-9",))
        assert "obs-9" in fp.superseded_observation_ids

    def test_negative_question_index_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_provenance(computed_at_question_index=-1)

    def test_empty_feature_engine_version_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_provenance(feature_engine_version="")

    def test_empty_updater_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_provenance(updater_id="")

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            _make_provenance(unknown="x")

    def test_immutability(self) -> None:
        fp = _make_provenance()
        with pytest.raises(ValidationError):
            fp.updater_id = "other"  # type: ignore[misc]

    def test_source_observation_ids_preserved_as_tuple(self) -> None:
        fp = _make_provenance(source_observation_ids=("obs-a", "obs-b", "obs-c"))
        assert fp.source_observation_ids == ("obs-a", "obs-b", "obs-c")

    def test_empty_source_observation_ids_allowed(self) -> None:
        fp = _make_provenance(source_observation_ids=())
        assert fp.source_observation_ids == ()

    def test_equality(self) -> None:
        a = _make_provenance()
        b = _make_provenance()
        assert a == b

    def test_inequality_different_updater(self) -> None:
        a = _make_provenance(updater_id="updater_a")
        b = _make_provenance(updater_id="updater_b")
        assert a != b

    def test_provenance_carries_feature_identity(self) -> None:
        fp = _make_provenance()
        assert fp.feature_identity.feature_type_id == "reasoning_feature"
