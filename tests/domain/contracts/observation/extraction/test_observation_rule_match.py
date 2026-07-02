# tests/domain/contracts/observation/extraction/test_observation_rule_match.py

import pytest
from pydantic import ValidationError

from domain.contracts.observation.extraction.observation_rule_match import ObservationRuleMatch
from domain.contracts.observation.observation_type import ObservationType


def _match(**kwargs) -> ObservationRuleMatch:
    defaults = dict(
        rule_id="rule-001",
        observation_type=ObservationType.TECHNICAL_CORRECTNESS,
        confidence=0.8,
        description="System-generated observation description.",
    )
    defaults.update(kwargs)
    return ObservationRuleMatch(**defaults)


class TestObservationRuleMatchDefaults:
    def test_tags_default_empty_frozenset(self):
        m = _match()
        assert m.tags == frozenset()

    def test_rationale_default_empty(self):
        m = _match()
        assert m.rationale == ""

    def test_schema_version_default(self):
        m = _match()
        assert m.schema_version == "1.0"


class TestObservationRuleMatchImmutability:
    def test_frozen(self):
        m = _match()
        with pytest.raises(ValidationError):
            m.confidence = 0.1

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            _match(extra="x")  # type: ignore[call-arg]


class TestObservationRuleMatchValidation:
    def test_rule_id_empty_raises(self):
        with pytest.raises(ValidationError):
            _match(rule_id="")

    def test_confidence_zero_valid(self):
        m = _match(confidence=0.0)
        assert m.confidence == 0.0

    def test_confidence_one_valid(self):
        m = _match(confidence=1.0)
        assert m.confidence == 1.0

    def test_confidence_below_zero_raises(self):
        with pytest.raises(ValidationError):
            _match(confidence=-0.01)

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValidationError):
            _match(confidence=1.01)

    def test_description_blank_raises(self):
        with pytest.raises(ValidationError):
            _match(description="   ")

    def test_description_stripped(self):
        m = _match(description="  leading spaces  ")
        assert m.description == "leading spaces"

    def test_description_max_length(self):
        m = _match(description="x" * 500)
        assert len(m.description) == 500

    def test_description_too_long_raises(self):
        with pytest.raises(ValidationError):
            _match(description="x" * 501)

    def test_description_empty_raises(self):
        with pytest.raises(ValidationError):
            _match(description="")

    def test_rationale_max_length(self):
        m = _match(rationale="r" * 1000)
        assert len(m.rationale) == 1000

    def test_rationale_too_long_raises(self):
        with pytest.raises(ValidationError):
            _match(rationale="r" * 1001)

    def test_tags_from_list(self):
        m = _match(tags=["python", "senior"])
        assert m.tags == frozenset({"python", "senior"})

    def test_tags_from_set(self):
        m = _match(tags={"a", "b"})
        assert "a" in m.tags

    def test_tags_none_becomes_empty(self):
        m = _match(tags=None)
        assert m.tags == frozenset()

    def test_tags_invalid_type_raises(self):
        with pytest.raises(ValidationError):
            _match(tags=123)  # type: ignore[arg-type]


class TestObservationRuleMatchFields:
    def test_rule_id_stored(self):
        m = _match(rule_id="my-rule")
        assert m.rule_id == "my-rule"

    def test_observation_type_stored(self):
        m = _match(observation_type=ObservationType.LEADERSHIP_STRONG)
        assert m.observation_type == ObservationType.LEADERSHIP_STRONG

    def test_all_observation_types_constructable(self):
        for otype in ObservationType:
            m = _match(observation_type=otype)
            assert m.observation_type == otype
