# tests/domain/profile/test_derivation_rules.py
# Focused tests for CandidateProfileDerivationRules (MIG-06 S-00)

import pytest
from pydantic import ValidationError

from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.profile._derivation_rules import (
    CandidateProfileDerivationRules,
    FeatureDimensionMapping,
    ValueProxyEntry,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def rules() -> CandidateProfileDerivationRules:
    return CandidateProfileDerivationRules.default()


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


class TestImmutability:
    def test_rules_is_frozen(self, rules: CandidateProfileDerivationRules) -> None:
        with pytest.raises((ValidationError, TypeError)):
            rules.rules_version = "tampered"  # type: ignore[misc]

    def test_feature_dimension_mapping_is_frozen(self) -> None:
        entry = FeatureDimensionMapping(
            feature_type=FeatureType.TECHNICAL_SKILL,
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            weight=1.0,
        )
        with pytest.raises((ValidationError, TypeError)):
            entry.weight = 0.5  # type: ignore[misc]

    def test_value_proxy_entry_is_frozen(self) -> None:
        entry = ValueProxyEntry(value_string="HIGH", numeric_score=85.0)
        with pytest.raises((ValidationError, TypeError)):
            entry.numeric_score = 0.0  # type: ignore[misc]

    def test_trend_override_eligible_features_is_frozenset(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        assert isinstance(rules.trend_override_eligible_features, frozenset)


# ---------------------------------------------------------------------------
# extra="forbid"
# ---------------------------------------------------------------------------


class TestExtraForbid:
    def test_extra_fields_raise_on_rules(self) -> None:
        with pytest.raises(ValidationError):
            CandidateProfileDerivationRules(  # type: ignore[call-arg]
                rules_version="1.0",
                feature_dimension_map=(
                    FeatureDimensionMapping(
                        feature_type=FeatureType.TECHNICAL_SKILL,
                        dimension=ProfileDimension.TECHNICAL_DEPTH,
                        weight=1.0,
                    ),
                ),
                value_proxy_table=(
                    ValueProxyEntry(value_string="*", numeric_score=50.0),
                ),
                min_evidence_for_trend=3,
                trend_threshold=8.0,
                max_evidence_confidence=10,
                low_confidence_max_evidence_modifier=8,
                low_confidence_threshold=0.3,
                areas_covered_min_confidence=0.3,
                areas_covered_allow_nascent=False,
                trend_override_eligible_features=frozenset(),
                trend_override_max_delta=8.0,
                unknown_extra_field="x",
            )

    def test_extra_fields_raise_on_mapping(self) -> None:
        with pytest.raises(ValidationError):
            FeatureDimensionMapping(  # type: ignore[call-arg]
                feature_type=FeatureType.TECHNICAL_SKILL,
                dimension=ProfileDimension.TECHNICAL_DEPTH,
                weight=1.0,
                unknown="x",
            )

    def test_extra_fields_raise_on_proxy_entry(self) -> None:
        with pytest.raises(ValidationError):
            ValueProxyEntry(value_string="HIGH", numeric_score=85.0, extra="x")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


class TestValidators:
    def _minimal_valid_kwargs(self) -> dict:
        return dict(
            rules_version="1.0",
            feature_dimension_map=(
                FeatureDimensionMapping(
                    feature_type=FeatureType.TECHNICAL_SKILL,
                    dimension=ProfileDimension.TECHNICAL_DEPTH,
                    weight=1.0,
                ),
            ),
            value_proxy_table=(
                ValueProxyEntry(value_string="*", numeric_score=50.0),
            ),
            min_evidence_for_trend=3,
            trend_threshold=8.0,
            max_evidence_confidence=10,
            low_confidence_max_evidence_modifier=8,
            low_confidence_threshold=0.3,
            areas_covered_min_confidence=0.3,
            areas_covered_allow_nascent=False,
            trend_override_eligible_features=frozenset(),
            trend_override_max_delta=8.0,
        )

    def test_weight_sum_exceeding_one_raises(self) -> None:
        kwargs = self._minimal_valid_kwargs()
        kwargs["feature_dimension_map"] = (
            FeatureDimensionMapping(
                feature_type=FeatureType.REASONING,
                dimension=ProfileDimension.PROBLEM_SOLVING,
                weight=0.7,
            ),
            FeatureDimensionMapping(
                feature_type=FeatureType.REASONING,
                dimension=ProfileDimension.ENGINEERING_JUDGMENT,
                weight=0.7,
            ),
        )
        with pytest.raises(ValidationError, match="total weight"):
            CandidateProfileDerivationRules(**kwargs)

    def test_weight_sum_equal_to_one_is_valid(self) -> None:
        kwargs = self._minimal_valid_kwargs()
        kwargs["feature_dimension_map"] = (
            FeatureDimensionMapping(
                feature_type=FeatureType.REASONING,
                dimension=ProfileDimension.PROBLEM_SOLVING,
                weight=0.7,
            ),
            FeatureDimensionMapping(
                feature_type=FeatureType.REASONING,
                dimension=ProfileDimension.ENGINEERING_JUDGMENT,
                weight=0.3,
            ),
        )
        rules = CandidateProfileDerivationRules(**kwargs)
        assert rules is not None

    def test_missing_fallback_in_proxy_table_raises(self) -> None:
        kwargs = self._minimal_valid_kwargs()
        kwargs["value_proxy_table"] = (
            ValueProxyEntry(value_string="HIGH", numeric_score=85.0),
        )
        with pytest.raises(ValidationError, match="fallback"):
            CandidateProfileDerivationRules(**kwargs)

    def test_two_fallbacks_in_proxy_table_raises(self) -> None:
        kwargs = self._minimal_valid_kwargs()
        kwargs["value_proxy_table"] = (
            ValueProxyEntry(value_string="*", numeric_score=50.0),
            ValueProxyEntry(value_string="*", numeric_score=55.0),
        )
        with pytest.raises(ValidationError, match="fallback"):
            CandidateProfileDerivationRules(**kwargs)

    def test_low_confidence_modifier_exceeds_max_raises(self) -> None:
        kwargs = self._minimal_valid_kwargs()
        kwargs["low_confidence_max_evidence_modifier"] = 15
        kwargs["max_evidence_confidence"] = 10
        with pytest.raises(ValidationError, match="low_confidence_max_evidence_modifier"):
            CandidateProfileDerivationRules(**kwargs)

    def test_min_evidence_must_be_at_least_2(self) -> None:
        kwargs = self._minimal_valid_kwargs()
        kwargs["min_evidence_for_trend"] = 1
        with pytest.raises(ValidationError):
            CandidateProfileDerivationRules(**kwargs)

    def test_trend_threshold_must_be_positive(self) -> None:
        kwargs = self._minimal_valid_kwargs()
        kwargs["trend_threshold"] = 0.0
        with pytest.raises(ValidationError):
            CandidateProfileDerivationRules(**kwargs)


# ---------------------------------------------------------------------------
# default() correctness
# ---------------------------------------------------------------------------


class TestDefaultRules:
    def test_version_is_1_2(self, rules: CandidateProfileDerivationRules) -> None:
        assert rules.rules_version == "1.2"

    def test_technical_skill_maps_to_technical_depth_weight_1(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        entries = [
            e
            for e in rules.feature_dimension_map
            if e.feature_type == FeatureType.TECHNICAL_SKILL
        ]
        assert len(entries) == 1
        assert entries[0].dimension == ProfileDimension.TECHNICAL_DEPTH
        assert entries[0].weight == 1.0

    def test_reasoning_splits_to_two_dimensions(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        entries = {
            e.dimension: e.weight
            for e in rules.feature_dimension_map
            if e.feature_type == FeatureType.REASONING
        }
        assert entries[ProfileDimension.PROBLEM_SOLVING] == pytest.approx(0.7)
        assert entries[ProfileDimension.ENGINEERING_JUDGMENT] == pytest.approx(0.3)

    def test_learning_splits_correctly(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        entries = {
            e.dimension: e.weight
            for e in rules.feature_dimension_map
            if e.feature_type == FeatureType.LEARNING
        }
        assert entries[ProfileDimension.PROBLEM_SOLVING] == pytest.approx(0.4)
        assert entries[ProfileDimension.TECHNICAL_DEPTH] == pytest.approx(0.6)

    def test_coverage_and_trend_not_in_feature_dimension_map(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        mapped_types = {e.feature_type for e in rules.feature_dimension_map}
        assert FeatureType.COVERAGE not in mapped_types
        assert FeatureType.TREND not in mapped_types
        assert FeatureType.CONFIDENCE not in mapped_types

    def test_value_proxy_high(self, rules: CandidateProfileDerivationRules) -> None:
        entry = next(e for e in rules.value_proxy_table if e.value_string == "HIGH")
        assert entry.numeric_score == pytest.approx(85.0)

    def test_value_proxy_low(self, rules: CandidateProfileDerivationRules) -> None:
        entry = next(e for e in rules.value_proxy_table if e.value_string == "LOW")
        assert entry.numeric_score == pytest.approx(20.0)

    def test_value_proxy_fallback(self, rules: CandidateProfileDerivationRules) -> None:
        entry = next(e for e in rules.value_proxy_table if e.value_string == "*")
        assert entry.numeric_score == pytest.approx(50.0)

    def test_min_evidence_for_trend(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        assert rules.min_evidence_for_trend == 3

    def test_trend_threshold(self, rules: CandidateProfileDerivationRules) -> None:
        assert rules.trend_threshold == pytest.approx(8.0)

    def test_max_evidence_confidence(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        assert rules.max_evidence_confidence == 10

    def test_low_confidence_modifier(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        assert rules.low_confidence_max_evidence_modifier == 8

    def test_low_confidence_threshold(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        assert rules.low_confidence_threshold == pytest.approx(0.3)

    def test_areas_covered_min_confidence(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        assert rules.areas_covered_min_confidence == pytest.approx(0.3)

    def test_areas_covered_allow_nascent_is_false(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        assert rules.areas_covered_allow_nascent is False

    def test_trend_override_eligible_features(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        assert rules.trend_override_eligible_features == frozenset({FeatureType.TREND})

    def test_trend_override_max_delta(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        assert rules.trend_override_max_delta == pytest.approx(8.0)


# ---------------------------------------------------------------------------
# Weight invariants
# ---------------------------------------------------------------------------


class TestWeightInvariants:
    def test_all_feature_types_weight_sum_at_most_one(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        by_feature: dict[FeatureType, float] = {}
        for entry in rules.feature_dimension_map:
            by_feature[entry.feature_type] = (
                by_feature.get(entry.feature_type, 0.0) + entry.weight
            )
        for ft, total in by_feature.items():
            assert total <= 1.0 + 1e-9, f"{ft.value} weight sum {total} > 1.0"

    def test_individual_weights_positive(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        for entry in rules.feature_dimension_map:
            assert entry.weight > 0.0


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


class TestSerialization:
    def test_model_dump_round_trip(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        data = rules.model_dump()
        assert data["rules_version"] == "1.2"
        assert isinstance(data["feature_dimension_map"], (list, tuple))

    def test_model_dump_json_round_trip(
        self, rules: CandidateProfileDerivationRules
    ) -> None:
        json_str = rules.model_dump_json()
        assert "1.2" in json_str
        assert "TECHNICAL_DEPTH" in json_str or "technical_depth" in json_str

    def test_default_called_twice_returns_equal_objects(self) -> None:
        r1 = CandidateProfileDerivationRules.default()
        r2 = CandidateProfileDerivationRules.default()
        assert r1 == r2
