# tests/domain/contracts/test_generation_metadata.py

import pytest
from pydantic import ValidationError

from domain.contracts.interview.generation_metadata import GenerationMetadata


def _valid_kwargs(**overrides) -> dict:
    base = {
        "total_tokens_used": 4200,
        "total_cost_usd": 0.084,
        "cost_per_question_usd": 0.0042,
    }
    base.update(overrides)
    return base


class TestGenerationMetadataConstruction:
    def test_valid_with_all_fields(self):
        gm = GenerationMetadata(**_valid_kwargs())
        assert gm.total_tokens_used == 4200
        assert gm.total_cost_usd == pytest.approx(0.084)
        assert gm.cost_per_question_usd == pytest.approx(0.0042)
        assert gm.schema_version == "1.0"

    def test_valid_cost_fields_none(self):
        gm = GenerationMetadata(total_tokens_used=1000, total_cost_usd=None, cost_per_question_usd=None)
        assert gm.total_cost_usd is None
        assert gm.cost_per_question_usd is None

    def test_cost_fields_default_to_none(self):
        gm = GenerationMetadata(total_tokens_used=500)
        assert gm.total_cost_usd is None
        assert gm.cost_per_question_usd is None

    def test_zero_tokens_valid(self):
        gm = GenerationMetadata(total_tokens_used=0)
        assert gm.total_tokens_used == 0

    def test_schema_version_default(self):
        gm = GenerationMetadata(total_tokens_used=100)
        assert gm.schema_version == "1.0"

    def test_custom_schema_version(self):
        gm = GenerationMetadata(total_tokens_used=100, schema_version="2.0")
        assert gm.schema_version == "2.0"

    def test_zero_cost_valid(self):
        gm = GenerationMetadata(**_valid_kwargs(total_cost_usd=0.0, cost_per_question_usd=0.0))
        assert gm.total_cost_usd == 0.0
        assert gm.cost_per_question_usd == 0.0


class TestGenerationMetadataFieldValidation:
    def test_negative_tokens_rejected(self):
        with pytest.raises(ValidationError):
            GenerationMetadata(total_tokens_used=-1)

    def test_negative_total_cost_rejected(self):
        with pytest.raises(ValidationError):
            GenerationMetadata(**_valid_kwargs(total_cost_usd=-0.001))

    def test_negative_cost_per_question_rejected(self):
        with pytest.raises(ValidationError):
            GenerationMetadata(**_valid_kwargs(cost_per_question_usd=-0.001))

    def test_empty_schema_version_rejected(self):
        with pytest.raises(ValidationError):
            GenerationMetadata(total_tokens_used=100, schema_version="")

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            GenerationMetadata(**_valid_kwargs(unknown_field="value"))


class TestGenerationMetadataImmutability:
    def test_total_tokens_assignment_raises(self):
        gm = GenerationMetadata(**_valid_kwargs())
        with pytest.raises((TypeError, ValidationError)):
            gm.total_tokens_used = 999  # type: ignore[misc]

    def test_total_cost_assignment_raises(self):
        gm = GenerationMetadata(**_valid_kwargs())
        with pytest.raises((TypeError, ValidationError)):
            gm.total_cost_usd = 0.0  # type: ignore[misc]

    def test_schema_version_assignment_raises(self):
        gm = GenerationMetadata(**_valid_kwargs())
        with pytest.raises((TypeError, ValidationError)):
            gm.schema_version = "2.0"  # type: ignore[misc]


class TestGenerationMetadataSerialization:
    def test_model_dump_contains_all_keys(self):
        gm = GenerationMetadata(**_valid_kwargs())
        data = gm.model_dump()
        assert set(data.keys()) == {"total_tokens_used", "total_cost_usd", "cost_per_question_usd", "schema_version"}

    def test_round_trip_with_all_fields(self):
        gm = GenerationMetadata(**_valid_kwargs())
        restored = GenerationMetadata.model_validate(gm.model_dump())
        assert restored == gm

    def test_round_trip_with_none_costs(self):
        gm = GenerationMetadata(total_tokens_used=100)
        restored = GenerationMetadata.model_validate(gm.model_dump())
        assert restored == gm

    def test_none_costs_serialized_as_none(self):
        gm = GenerationMetadata(total_tokens_used=100)
        data = gm.model_dump()
        assert data["total_cost_usd"] is None
        assert data["cost_per_question_usd"] is None


class TestGenerationMetadataEquality:
    def test_equal_instances(self):
        a = GenerationMetadata(**_valid_kwargs())
        b = GenerationMetadata(**_valid_kwargs())
        assert a == b

    def test_different_tokens_not_equal(self):
        a = GenerationMetadata(**_valid_kwargs(total_tokens_used=100))
        b = GenerationMetadata(**_valid_kwargs(total_tokens_used=200))
        assert a != b

    def test_none_vs_zero_cost_not_equal(self):
        a = GenerationMetadata(total_tokens_used=100, total_cost_usd=None)
        b = GenerationMetadata(total_tokens_used=100, total_cost_usd=0.0)
        assert a != b
