# tests/domain/profile/test_derived_profile_data.py
# Focused tests for DerivedProfileData (MIG-06 S-01)

import pytest
from pydantic import ValidationError

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.feature.feature_quality import (
    FeatureConfidence,
    FeatureMaturity,
    FeatureQuality,
    FeatureStability,
)
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from domain.profile._derived_profile_data import DerivedProfileData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _trace(
    average_score: float = 60.0,
    evidence_count: int = 3,
    trend: Trend = Trend.STABLE,
    last_score: float | None = None,
    confidence: float = 0.5,
) -> DimensionTrace:
    return DimensionTrace(
        average_score=average_score,
        last_score=last_score if last_score is not None else average_score,
        trend=trend,
        confidence=confidence,
        evidence_count=evidence_count,
        last_updated_question=0,
    )


def _feature(
    feature_type: FeatureType = FeatureType.TECHNICAL_SKILL,
    value: str = "HIGH",
    computed_at: int = 0,
) -> ProfileFeature:
    identity = FeatureIdentity.for_type(feature_type)
    return ProfileFeature(
        feature_identity=identity,
        value=value,
        quality=FeatureQuality(
            confidence=FeatureConfidence(value=0.8),
            stability=FeatureStability(state="stable"),
            maturity=FeatureMaturity.from_observation_count(3),
        ),
        computed_at_question_index=computed_at,
        provenance=FeatureProvenance(
            feature_identity=identity,
            computed_at_question_index=computed_at,
            feature_engine_version="1.0",
            updater_id="test_updater",
        ),
        candidate_identity_id="test-candidate-001",
    )


def _minimal_valid(
    dimension_scores: dict[ProfileDimension, DimensionTrace] | None = None,
    questions_answered: int = 1,
    coverage_ratio: float | None = None,
    dominant_dimension: ProfileDimension | None = None,
    weakest_dimension: ProfileDimension | None = None,
    source_features: tuple[ProfileFeature, ...] = (),
    last_updated_at_question_index: int = -1,
    areas_covered: list[str] | None = None,
) -> DerivedProfileData:
    scores = dimension_scores or {}
    scored_count = sum(1 for t in scores.values() if t.evidence_count >= 1)
    ratio = coverage_ratio if coverage_ratio is not None else round(
        scored_count / len(ProfileDimension), 4
    )
    return DerivedProfileData(
        dimension_scores=scores,
        questions_answered=questions_answered,
        areas_covered=areas_covered or [],
        coverage_ratio=ratio,
        dominant_dimension=dominant_dimension,
        weakest_dimension=weakest_dimension,
        source_features=source_features,
        last_updated_at_question_index=last_updated_at_question_index,
    )


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


class TestImmutability:
    def test_frozen(self) -> None:
        data = _minimal_valid()
        with pytest.raises((ValidationError, TypeError)):
            data.questions_answered = 99  # type: ignore[misc]

    def test_field_reassignment_raises(self) -> None:
        data = _minimal_valid(
            dimension_scores={ProfileDimension.TECHNICAL_DEPTH: _trace()},
            dominant_dimension=ProfileDimension.TECHNICAL_DEPTH,
            weakest_dimension=None,
            coverage_ratio=round(1 / 5, 4),
        )
        with pytest.raises((ValidationError, TypeError)):
            data.dimension_scores = {}  # type: ignore[misc]

    def test_source_features_is_tuple(self) -> None:
        f = _feature()
        data = _minimal_valid(
            source_features=(f,),
            last_updated_at_question_index=0,
        )
        assert isinstance(data.source_features, tuple)


# ---------------------------------------------------------------------------
# extra="forbid"
# ---------------------------------------------------------------------------


class TestExtraForbid:
    def test_extra_field_raises(self) -> None:
        with pytest.raises(ValidationError):
            DerivedProfileData(  # type: ignore[call-arg]
                questions_answered=0,
                coverage_ratio=0.0,
                unknown_field="x",
            )


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


class TestValidators:
    def test_dominant_not_in_scores_raises(self) -> None:
        with pytest.raises(ValidationError, match="dominant_dimension"):
            _minimal_valid(
                dominant_dimension=ProfileDimension.TECHNICAL_DEPTH,
            )

    def test_weakest_not_in_scores_raises(self) -> None:
        with pytest.raises(ValidationError, match="weakest_dimension"):
            _minimal_valid(
                weakest_dimension=ProfileDimension.COMMUNICATION,
            )

    def test_dominant_equals_weakest_with_multiple_dimensions_raises(self) -> None:
        scores = {
            ProfileDimension.TECHNICAL_DEPTH: _trace(evidence_count=5),
            ProfileDimension.COMMUNICATION: _trace(evidence_count=3),
        }
        ratio = round(2 / 5, 4)
        with pytest.raises(ValidationError, match="must differ"):
            DerivedProfileData(
                dimension_scores=scores,
                questions_answered=1,
                areas_covered=[],
                coverage_ratio=ratio,
                dominant_dimension=ProfileDimension.TECHNICAL_DEPTH,
                weakest_dimension=ProfileDimension.TECHNICAL_DEPTH,
                source_features=(),
                last_updated_at_question_index=-1,
            )

    def test_dominant_equals_weakest_single_dimension_is_valid(self) -> None:
        scores = {ProfileDimension.TECHNICAL_DEPTH: _trace(evidence_count=3)}
        ratio = round(1 / 5, 4)
        data = DerivedProfileData(
            dimension_scores=scores,
            questions_answered=1,
            areas_covered=[],
            coverage_ratio=ratio,
            dominant_dimension=ProfileDimension.TECHNICAL_DEPTH,
            weakest_dimension=ProfileDimension.TECHNICAL_DEPTH,
            source_features=(),
            last_updated_at_question_index=-1,
        )
        assert data.dominant_dimension == data.weakest_dimension

    def test_coverage_ratio_mismatch_raises(self) -> None:
        scores = {ProfileDimension.TECHNICAL_DEPTH: _trace(evidence_count=2)}
        with pytest.raises(ValidationError, match="coverage_ratio"):
            DerivedProfileData(
                dimension_scores=scores,
                questions_answered=1,
                areas_covered=[],
                coverage_ratio=0.9999,
                dominant_dimension=ProfileDimension.TECHNICAL_DEPTH,
                weakest_dimension=None,
                source_features=(),
                last_updated_at_question_index=-1,
            )

    def test_last_updated_mismatch_with_features_raises(self) -> None:
        f = _feature(computed_at=5)
        with pytest.raises(ValidationError, match="last_updated_at_question_index"):
            DerivedProfileData(
                dimension_scores={},
                questions_answered=1,
                areas_covered=[],
                coverage_ratio=0.0,
                dominant_dimension=None,
                weakest_dimension=None,
                source_features=(f,),
                last_updated_at_question_index=3,
            )

    def test_last_updated_nonzero_with_empty_features_raises(self) -> None:
        with pytest.raises(ValidationError, match="last_updated_at_question_index"):
            DerivedProfileData(
                dimension_scores={},
                questions_answered=0,
                areas_covered=[],
                coverage_ratio=0.0,
                dominant_dimension=None,
                weakest_dimension=None,
                source_features=(),
                last_updated_at_question_index=2,
            )

    def test_areas_covered_unsorted_raises(self) -> None:
        with pytest.raises(ValidationError, match="sorted"):
            _minimal_valid(areas_covered=["z_area", "a_area"])

    def test_areas_covered_duplicates_raises(self) -> None:
        with pytest.raises(ValidationError, match="unique"):
            _minimal_valid(areas_covered=["area_a", "area_a"])

    def test_questions_answered_negative_raises(self) -> None:
        with pytest.raises(ValidationError):
            DerivedProfileData(
                dimension_scores={},
                questions_answered=-1,
                areas_covered=[],
                coverage_ratio=0.0,
                dominant_dimension=None,
                weakest_dimension=None,
                source_features=(),
                last_updated_at_question_index=-1,
            )


# ---------------------------------------------------------------------------
# Valid construction
# ---------------------------------------------------------------------------


class TestValidConstruction:
    def test_empty_is_valid(self) -> None:
        data = _minimal_valid()
        assert data.questions_answered == 1
        assert data.dimension_scores == {}
        assert data.coverage_ratio == 0.0
        assert data.dominant_dimension is None
        assert data.weakest_dimension is None

    def test_single_dimension(self) -> None:
        scores = {ProfileDimension.TECHNICAL_DEPTH: _trace(average_score=75.0)}
        f = _feature(computed_at=2)
        data = DerivedProfileData(
            dimension_scores=scores,
            questions_answered=1,
            areas_covered=["technical_knowledge"],
            coverage_ratio=round(1 / 5, 4),
            dominant_dimension=ProfileDimension.TECHNICAL_DEPTH,
            weakest_dimension=ProfileDimension.TECHNICAL_DEPTH,
            source_features=(f,),
            last_updated_at_question_index=2,
        )
        assert data.dimension_scores[ProfileDimension.TECHNICAL_DEPTH].average_score == 75.0

    def test_multiple_dimensions(self) -> None:
        scores = {
            ProfileDimension.TECHNICAL_DEPTH: _trace(average_score=80.0, evidence_count=4),
            ProfileDimension.COMMUNICATION: _trace(average_score=50.0, evidence_count=2),
        }
        data = DerivedProfileData(
            dimension_scores=scores,
            questions_answered=3,
            areas_covered=["technical_knowledge"],
            coverage_ratio=round(2 / 5, 4),
            dominant_dimension=ProfileDimension.TECHNICAL_DEPTH,
            weakest_dimension=ProfileDimension.COMMUNICATION,
            source_features=(),
            last_updated_at_question_index=-1,
        )
        assert data.coverage_ratio == pytest.approx(0.4)

    def test_source_features_preserved_verbatim(self) -> None:
        f0 = _feature(computed_at=0)
        f1 = _feature(feature_type=FeatureType.REASONING, computed_at=3)
        data = DerivedProfileData(
            dimension_scores={},
            questions_answered=2,
            areas_covered=[],
            coverage_ratio=0.0,
            dominant_dimension=None,
            weakest_dimension=None,
            source_features=(f0, f1),
            last_updated_at_question_index=3,
        )
        assert data.source_features == (f0, f1)

    def test_coverage_ratio_all_five_dimensions(self) -> None:
        scores = {d: _trace(evidence_count=1) for d in ProfileDimension}
        data = DerivedProfileData(
            dimension_scores=scores,
            questions_answered=5,
            areas_covered=[],
            coverage_ratio=1.0,
            dominant_dimension=None,
            weakest_dimension=None,
            source_features=(),
            last_updated_at_question_index=-1,
        )
        assert data.coverage_ratio == 1.0


# ---------------------------------------------------------------------------
# Equality
# ---------------------------------------------------------------------------


class TestEquality:
    def test_equal_instances(self) -> None:
        d1 = _minimal_valid()
        d2 = _minimal_valid()
        assert d1 == d2

    def test_unequal_on_different_questions_answered(self) -> None:
        d1 = _minimal_valid(questions_answered=1)
        d2 = _minimal_valid(questions_answered=2)
        assert d1 != d2


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


class TestSerialization:
    def test_model_dump_contains_expected_keys(self) -> None:
        data = _minimal_valid()
        dumped = data.model_dump()
        assert "dimension_scores" in dumped
        assert "questions_answered" in dumped
        assert "coverage_ratio" in dumped
        assert "dominant_dimension" in dumped
        assert "weakest_dimension" in dumped
        assert "areas_covered" in dumped
        assert "source_features" in dumped
        assert "last_updated_at_question_index" in dumped

    def test_model_dump_json_round_trip(self) -> None:
        data = _minimal_valid(questions_answered=3)
        json_str = data.model_dump_json()
        assert "questions_answered" in json_str
        assert "coverage_ratio" in json_str
