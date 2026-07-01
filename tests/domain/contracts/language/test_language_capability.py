# tests/domain/contracts/language/test_language_capability.py

import pytest
from pydantic import ValidationError

from domain.contracts.language.language_capability import LanguageCapability


def _make_cap(**overrides) -> LanguageCapability:
    defaults = dict(language_id="python")
    defaults.update(overrides)
    return LanguageCapability(**defaults)


class TestLanguageCapabilityConstruction:
    def test_minimal(self):
        cap = _make_cap()
        assert cap.language_id == "python"
        assert cap.questions_answered_in_language == 0
        assert cap.composite_score == 0.0
        assert cap.idiomatic_usage_score == 0.0
        assert cap.type_error_rate == 0.0
        assert cap.schema_version == "1.0"

    def test_full_construction(self):
        cap = _make_cap(
            language_id="javascript",
            questions_answered_in_language=3,
            composite_score=0.75,
            idiomatic_usage_score=0.8,
            type_error_rate=0.1,
        )
        assert cap.composite_score == 0.75
        assert cap.questions_answered_in_language == 3

    def test_score_boundary_zero(self):
        cap = _make_cap(composite_score=0.0)
        assert cap.composite_score == 0.0

    def test_score_boundary_one(self):
        cap = _make_cap(composite_score=1.0)
        assert cap.composite_score == 1.0


class TestLanguageCapabilityValidation:
    def test_empty_language_id_rejected(self):
        with pytest.raises(ValidationError):
            _make_cap(language_id="")

    def test_composite_score_above_one_rejected(self):
        with pytest.raises(ValidationError):
            _make_cap(composite_score=1.1)

    def test_composite_score_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _make_cap(composite_score=-0.1)

    def test_idiomatic_usage_above_one_rejected(self):
        with pytest.raises(ValidationError):
            _make_cap(idiomatic_usage_score=1.5)

    def test_type_error_rate_above_one_rejected(self):
        with pytest.raises(ValidationError):
            _make_cap(type_error_rate=2.0)

    def test_questions_answered_negative_rejected(self):
        with pytest.raises(ValidationError):
            _make_cap(questions_answered_in_language=-1)

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            _make_cap(sandbox_type="docker")


class TestLanguageCapabilityImmutability:
    def test_composite_score_frozen(self):
        cap = _make_cap()
        with pytest.raises((ValidationError, TypeError)):
            cap.composite_score = 0.9


class TestLanguageCapabilitySerialization:
    def test_roundtrip(self):
        cap = _make_cap(composite_score=0.6, questions_answered_in_language=2)
        data = cap.model_dump()
        cap2 = LanguageCapability(**data)
        assert cap == cap2

    def test_json_roundtrip(self):
        cap = _make_cap(idiomatic_usage_score=0.7)
        json_str = cap.model_dump_json()
        cap2 = LanguageCapability.model_validate_json(json_str)
        assert cap == cap2
