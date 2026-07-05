# tests/domain/contracts/report/test_scoring_dimension.py

import pytest
from pydantic import ValidationError

from domain.contracts.report.scoring_dimension import ScoringDimension
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType


def _valid_kwargs(**overrides) -> dict:
    base = {
        "dimension_type": PerformanceDimensionType.TECHNICAL_DEPTH,
        "score": 75.0,
        "signal": 0.8,
        "weighted_contribution": 0.2,
        "justification": "Demonstrated solid technical depth across all questions.",
        "level": "strong",
    }
    base.update(overrides)
    return base


class TestScoringDimensionConstruction:
    def test_valid_construction(self):
        dim = ScoringDimension(**_valid_kwargs())
        assert dim.dimension_type == PerformanceDimensionType.TECHNICAL_DEPTH
        assert dim.score == 75.0
        assert dim.signal == 0.8
        assert dim.weighted_contribution == 0.2
        assert dim.justification == "Demonstrated solid technical depth across all questions."
        assert dim.level == "strong"

    def test_all_dimension_types_accepted(self):
        for dt in PerformanceDimensionType:
            dim = ScoringDimension(**_valid_kwargs(dimension_type=dt))
            assert dim.dimension_type == dt

    def test_all_valid_levels_accepted(self):
        for level in ("strong", "moderate", "weak"):
            dim = ScoringDimension(**_valid_kwargs(level=level))
            assert dim.level == level

    def test_boundary_score_zero(self):
        dim = ScoringDimension(**_valid_kwargs(score=0.0))
        assert dim.score == 0.0

    def test_boundary_score_hundred(self):
        dim = ScoringDimension(**_valid_kwargs(score=100.0))
        assert dim.score == 100.0

    def test_boundary_signal_zero(self):
        dim = ScoringDimension(**_valid_kwargs(signal=0.0))
        assert dim.signal == 0.0

    def test_boundary_signal_one(self):
        dim = ScoringDimension(**_valid_kwargs(signal=1.0))
        assert dim.signal == 1.0

    def test_boundary_weighted_contribution_zero(self):
        dim = ScoringDimension(**_valid_kwargs(weighted_contribution=0.0))
        assert dim.weighted_contribution == 0.0

    def test_boundary_weighted_contribution_one(self):
        dim = ScoringDimension(**_valid_kwargs(weighted_contribution=1.0))
        assert dim.weighted_contribution == 1.0


class TestScoringDimensionFieldValidation:
    def test_score_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            ScoringDimension(**_valid_kwargs(score=-0.1))

    def test_score_above_hundred_rejected(self):
        with pytest.raises(ValidationError):
            ScoringDimension(**_valid_kwargs(score=100.1))

    def test_signal_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            ScoringDimension(**_valid_kwargs(signal=-0.01))

    def test_signal_above_one_rejected(self):
        with pytest.raises(ValidationError):
            ScoringDimension(**_valid_kwargs(signal=1.01))

    def test_weighted_contribution_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            ScoringDimension(**_valid_kwargs(weighted_contribution=-0.01))

    def test_weighted_contribution_above_one_rejected(self):
        with pytest.raises(ValidationError):
            ScoringDimension(**_valid_kwargs(weighted_contribution=1.01))

    def test_empty_justification_rejected(self):
        with pytest.raises(ValidationError):
            ScoringDimension(**_valid_kwargs(justification=""))

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            ScoringDimension(**_valid_kwargs(unknown_field="value"))


class TestScoringDimensionInvariants:
    def test_invalid_level_rejected(self):
        with pytest.raises(ValidationError):
            ScoringDimension(**_valid_kwargs(level="excellent"))

    def test_level_case_sensitive(self):
        with pytest.raises(ValidationError):
            ScoringDimension(**_valid_kwargs(level="Strong"))

    def test_empty_level_rejected(self):
        with pytest.raises(ValidationError):
            ScoringDimension(**_valid_kwargs(level=""))


class TestScoringDimensionImmutability:
    def test_score_assignment_raises(self):
        dim = ScoringDimension(**_valid_kwargs())
        with pytest.raises((TypeError, ValidationError)):
            dim.score = 50.0  # type: ignore[misc]

    def test_level_assignment_raises(self):
        dim = ScoringDimension(**_valid_kwargs())
        with pytest.raises((TypeError, ValidationError)):
            dim.level = "weak"  # type: ignore[misc]

    def test_justification_assignment_raises(self):
        dim = ScoringDimension(**_valid_kwargs())
        with pytest.raises((TypeError, ValidationError)):
            dim.justification = "changed"  # type: ignore[misc]


class TestScoringDimensionSerialization:
    def test_model_dump_contains_all_fields(self):
        dim = ScoringDimension(**_valid_kwargs())
        data = dim.model_dump()
        assert "dimension_type" in data
        assert "score" in data
        assert "signal" in data
        assert "weighted_contribution" in data
        assert "justification" in data
        assert "level" in data

    def test_model_dump_dimension_type_as_value(self):
        dim = ScoringDimension(**_valid_kwargs())
        data = dim.model_dump()
        assert data["dimension_type"] == PerformanceDimensionType.TECHNICAL_DEPTH

    def test_round_trip_via_model_validate(self):
        dim = ScoringDimension(**_valid_kwargs())
        restored = ScoringDimension.model_validate(dim.model_dump())
        assert restored == dim


class TestScoringDimensionEquality:
    def test_equal_instances(self):
        a = ScoringDimension(**_valid_kwargs())
        b = ScoringDimension(**_valid_kwargs())
        assert a == b

    def test_different_score_not_equal(self):
        a = ScoringDimension(**_valid_kwargs(score=70.0))
        b = ScoringDimension(**_valid_kwargs(score=80.0))
        assert a != b

    def test_different_level_not_equal(self):
        a = ScoringDimension(**_valid_kwargs(level="strong"))
        b = ScoringDimension(**_valid_kwargs(level="weak"))
        assert a != b
