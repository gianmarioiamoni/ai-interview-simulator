# tests/domain/contracts/feature/test_feature_quality.py

import pytest
from pydantic import ValidationError

from domain.contracts.feature.feature_quality import (
    MATURITY_DEVELOPING,
    MATURITY_MATURE,
    MATURITY_NASCENT,
    STABILITY_EMERGING,
    STABILITY_STABLE,
    STABILITY_UNSTABLE,
    FeatureConfidence,
    FeatureMaturity,
    FeatureQuality,
    FeatureStability,
)


class TestFeatureConfidence:
    def test_valid_midpoint(self) -> None:
        fc = FeatureConfidence(value=0.5)
        assert fc.value == 0.5

    def test_boundary_zero(self) -> None:
        fc = FeatureConfidence(value=0.0)
        assert fc.value == 0.0

    def test_boundary_one(self) -> None:
        fc = FeatureConfidence(value=1.0)
        assert fc.value == 1.0

    def test_below_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FeatureConfidence(value=-0.01)

    def test_above_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FeatureConfidence(value=1.01)

    def test_is_low_below_threshold(self) -> None:
        assert FeatureConfidence(value=0.29).is_low is True

    def test_is_low_at_threshold_boundary(self) -> None:
        assert FeatureConfidence(value=0.3).is_low is False

    def test_is_low_above_threshold(self) -> None:
        assert FeatureConfidence(value=0.8).is_low is False

    def test_default_schema_version(self) -> None:
        fc = FeatureConfidence(value=0.5)
        assert fc.schema_version == "1.0"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            FeatureConfidence(value=0.5, extra="x")

    def test_immutable(self) -> None:
        fc = FeatureConfidence(value=0.5)
        with pytest.raises(ValidationError):
            fc.value = 0.9  # type: ignore[misc]


class TestFeatureStability:
    @pytest.mark.parametrize("state", ["stable", "unstable", "emerging"])
    def test_valid_states(self, state: str) -> None:
        fs = FeatureStability(state=state)
        assert fs.state == state

    def test_invalid_state_rejected(self) -> None:
        with pytest.raises(ValueError):
            FeatureStability(state="unknown_state")

    def test_default_schema_version(self) -> None:
        fs = FeatureStability(state="stable")
        assert fs.schema_version == "1.0"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            FeatureStability(state="stable", extra="x")

    def test_immutable(self) -> None:
        fs = FeatureStability(state="stable")
        with pytest.raises(ValidationError):
            fs.state = "unstable"  # type: ignore[misc]

    def test_state_constants(self) -> None:
        assert STABILITY_STABLE == "stable"
        assert STABILITY_UNSTABLE == "unstable"
        assert STABILITY_EMERGING == "emerging"

    def test_equality(self) -> None:
        a = FeatureStability(state="stable")
        b = FeatureStability(state="stable")
        assert a == b

    def test_inequality(self) -> None:
        assert FeatureStability(state="stable") != FeatureStability(state="unstable")


class TestFeatureMaturity:
    @pytest.mark.parametrize("stage", ["nascent", "developing", "mature"])
    def test_valid_stages(self, stage: str) -> None:
        fm = FeatureMaturity(stage=stage, observation_count=3)
        assert fm.stage == stage

    def test_invalid_stage_rejected(self) -> None:
        with pytest.raises(ValueError):
            FeatureMaturity(stage="unknown", observation_count=3)

    def test_observation_count_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FeatureMaturity(stage="nascent", observation_count=0)

    def test_observation_count_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FeatureMaturity(stage="nascent", observation_count=-1)

    def test_default_schema_version(self) -> None:
        fm = FeatureMaturity(stage="nascent", observation_count=1)
        assert fm.schema_version == "1.0"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            FeatureMaturity(stage="nascent", observation_count=1, extra="x")

    def test_immutable(self) -> None:
        fm = FeatureMaturity(stage="nascent", observation_count=1)
        with pytest.raises(ValidationError):
            fm.stage = "mature"  # type: ignore[misc]

    def test_stage_constants(self) -> None:
        assert MATURITY_NASCENT == "nascent"
        assert MATURITY_DEVELOPING == "developing"
        assert MATURITY_MATURE == "mature"

    @pytest.mark.parametrize(
        "count,expected_stage",
        [
            (1, "nascent"),
            (2, "nascent"),
            (3, "developing"),
            (5, "developing"),
            (6, "mature"),
            (20, "mature"),
        ],
    )
    def test_from_observation_count(self, count: int, expected_stage: str) -> None:
        fm = FeatureMaturity.from_observation_count(count)
        assert fm.stage == expected_stage
        assert fm.observation_count == count

    def test_from_observation_count_zero_raises(self) -> None:
        with pytest.raises(ValueError):
            FeatureMaturity.from_observation_count(0)

    def test_from_observation_count_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            FeatureMaturity.from_observation_count(-1)


class TestFeatureQuality:
    def _make_quality(self) -> FeatureQuality:
        return FeatureQuality(
            confidence=FeatureConfidence(value=0.75),
            stability=FeatureStability(state="stable"),
            maturity=FeatureMaturity(stage="developing", observation_count=4),
        )

    def test_construction(self) -> None:
        fq = self._make_quality()
        assert fq.confidence.value == 0.75
        assert fq.stability.state == "stable"
        assert fq.maturity.stage == "developing"

    def test_default_schema_version(self) -> None:
        fq = self._make_quality()
        assert fq.schema_version == "1.0"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            FeatureQuality(
                confidence=FeatureConfidence(value=0.5),
                stability=FeatureStability(state="stable"),
                maturity=FeatureMaturity(stage="nascent", observation_count=1),
                extra="x",
            )

    def test_immutable(self) -> None:
        fq = self._make_quality()
        with pytest.raises(ValidationError):
            fq.confidence = FeatureConfidence(value=0.1)  # type: ignore[misc]

    def test_equality(self) -> None:
        a = self._make_quality()
        b = self._make_quality()
        assert a == b
