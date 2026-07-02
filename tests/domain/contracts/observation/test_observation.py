# tests/domain/contracts/observation/test_observation.py

import pytest
from pydantic import ValidationError

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_id import ObservationId
from domain.contracts.observation.observation_metadata import ObservationMetadata
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType


def _meta(question_index: int = 0, session_id: str = "sess-001") -> ObservationMetadata:
    return ObservationMetadata(
        question_index=question_index,
        session_id=session_id,
        origin=ObservationOrigin.EVALUATION,
        source_ref="eval-001",
    )


def _obs(**kwargs) -> Observation:
    defaults = dict(
        observation_type=ObservationType.TECHNICAL_CORRECTNESS,
        metadata=_meta(),
        description="Clean solution with correct edge-case handling.",
        confidence=0.9,
    )
    defaults.update(kwargs)
    return Observation(**defaults)


class TestObservationDefaults:
    def test_id_auto_generated(self):
        obs = _obs()
        assert obs.id is not None
        assert isinstance(obs.id, ObservationId)

    def test_status_defaults_active(self):
        obs = _obs()
        assert obs.status == ObservationStatus.ACTIVE

    def test_weight_defaults_one(self):
        obs = _obs()
        assert obs.weight == 1.0

    def test_tags_defaults_empty_frozenset(self):
        obs = _obs()
        assert obs.tags == frozenset()

    def test_schema_version_default(self):
        obs = _obs()
        assert obs.schema_version == "1.0"


class TestObservationImmutability:
    def test_frozen(self):
        obs = _obs()
        with pytest.raises(ValidationError):
            obs.confidence = 0.5

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            Observation(
                observation_type=ObservationType.TECHNICAL_CORRECTNESS,
                metadata=_meta(),
                description="test",
                confidence=0.5,
                unexpected="field",  # type: ignore[call-arg]
            )


class TestObservationValidation:
    def test_confidence_zero_valid(self):
        obs = _obs(confidence=0.0)
        assert obs.confidence == 0.0

    def test_confidence_one_valid(self):
        obs = _obs(confidence=1.0)
        assert obs.confidence == 1.0

    def test_confidence_below_zero_raises(self):
        with pytest.raises(ValidationError):
            _obs(confidence=-0.01)

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValidationError):
            _obs(confidence=1.01)

    def test_weight_must_be_positive(self):
        with pytest.raises(ValidationError):
            _obs(weight=0.0)

    def test_weight_one_valid(self):
        obs = _obs(weight=1.0)
        assert obs.weight == 1.0

    def test_weight_small_positive_valid(self):
        obs = _obs(weight=0.001)
        assert obs.weight == pytest.approx(0.001)

    def test_weight_above_one_raises(self):
        with pytest.raises(ValidationError):
            _obs(weight=1.01)

    def test_description_blank_raises(self):
        with pytest.raises(ValidationError):
            _obs(description="   ")

    def test_description_stripped(self):
        obs = _obs(description="  hello  ")
        assert obs.description == "hello"

    def test_description_max_length(self):
        obs = _obs(description="x" * 500)
        assert len(obs.description) == 500

    def test_description_too_long_raises(self):
        with pytest.raises(ValidationError):
            _obs(description="x" * 501)

    def test_description_empty_raises(self):
        with pytest.raises(ValidationError):
            _obs(description="")

    def test_tags_from_list(self):
        obs = _obs(tags=["tag1", "tag2"])
        assert obs.tags == frozenset({"tag1", "tag2"})

    def test_tags_from_set(self):
        obs = _obs(tags={"a", "b"})
        assert "a" in obs.tags

    def test_tags_frozenset_stored(self):
        obs = _obs(tags=frozenset({"x"}))
        assert isinstance(obs.tags, frozenset)

    def test_tags_none_becomes_empty(self):
        obs = _obs(tags=None)
        assert obs.tags == frozenset()

    def test_tags_invalid_type_raises(self):
        with pytest.raises(ValidationError):
            _obs(tags="single_string")  # type: ignore[arg-type]


class TestObservationWithMethods:
    def test_with_status_returns_new_instance(self):
        obs = _obs()
        decayed = obs.with_status(ObservationStatus.DECAYED)
        assert decayed is not obs
        assert decayed.status == ObservationStatus.DECAYED

    def test_with_status_preserves_other_fields(self):
        obs = _obs(confidence=0.8)
        decayed = obs.with_status(ObservationStatus.DECAYED)
        assert decayed.confidence == 0.8
        assert decayed.id == obs.id

    def test_with_weight_returns_new_instance(self):
        obs = _obs()
        lighter = obs.with_weight(0.5)
        assert lighter is not obs
        assert lighter.weight == pytest.approx(0.5)

    def test_with_weight_preserves_other_fields(self):
        obs = _obs(description="test desc")
        lighter = obs.with_weight(0.3)
        assert lighter.description == "test desc"

    def test_original_unchanged_after_with_status(self):
        obs = _obs()
        obs.with_status(ObservationStatus.EXPIRED)
        assert obs.status == ObservationStatus.ACTIVE

    def test_original_unchanged_after_with_weight(self):
        obs = _obs()
        obs.with_weight(0.5)
        assert obs.weight == 1.0


class TestObservationTypes:
    def test_observation_type_stored(self):
        obs = _obs(observation_type=ObservationType.LEADERSHIP_STRONG)
        assert obs.observation_type == ObservationType.LEADERSHIP_STRONG

    def test_all_observation_types_constructable(self):
        for otype in ObservationType:
            o = _obs(observation_type=otype)
            assert o.observation_type == otype
