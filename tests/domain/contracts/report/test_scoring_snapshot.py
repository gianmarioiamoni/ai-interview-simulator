# tests/domain/contracts/report/test_scoring_snapshot.py

import pytest
from pydantic import ValidationError

from domain.contracts.feedback.confidence import Confidence
from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.report.scoring_dimension import ScoringDimension
from domain.contracts.report.scoring_snapshot import ScoringSnapshot
from domain.contracts.report.scoring_snapshot_builder import ScoringSnapshotBuilder
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_dimension(
    dim_type: PerformanceDimensionType = PerformanceDimensionType.TECHNICAL_DEPTH,
    score: float = 75.0,
    signal: float = 0.8,
    weighted_contribution: float = 0.2,
    justification: str = "Good technical depth.",
    level: str = "strong",
) -> ScoringDimension:
    return ScoringDimension(
        dimension_type=dim_type,
        score=score,
        signal=signal,
        weighted_contribution=weighted_contribution,
        justification=justification,
        level=level,
    )


def _make_two_dimensions() -> tuple[ScoringDimension, ScoringDimension]:
    return (
        _make_dimension(PerformanceDimensionType.TECHNICAL_DEPTH, score=75.0, signal=0.8, weighted_contribution=0.3),
        _make_dimension(PerformanceDimensionType.PROBLEM_SOLVING, score=60.0, signal=0.6, weighted_contribution=0.25, level="moderate"),
    )


def _base_builder(dimensions: tuple[ScoringDimension, ...] | None = None) -> ScoringSnapshotBuilder:
    dims = dimensions if dimensions is not None else (_make_dimension(),)
    return (
        ScoringSnapshotBuilder()
        .with_overall_score(72.5)
        .with_scoring_dimensions(dims)
        .with_level(InterviewLevel.STRONG)
        .with_hire_decision(HireDecision.HIRE)
        .with_hiring_probability(78.0)
        .with_percentile_rank(65.0)
        .with_percentile_explanation("Better than 65% of candidates.")
        .with_decision_explanation({"strengths": ["Good problem solving"], "gaps": ["System design"]})
        .with_gating(triggered=False)
        .with_confidence(Confidence(base=0.85, final=0.80))
    )


# ---------------------------------------------------------------------------
# Builder — basic construction
# ---------------------------------------------------------------------------


class TestScoringSnapshotBuilderConstruction:
    def test_builds_valid_snapshot(self):
        snapshot = _base_builder().build()
        assert isinstance(snapshot, ScoringSnapshot)

    def test_overall_score_set(self):
        snapshot = _base_builder().build()
        assert snapshot.overall_score == 72.5

    def test_hire_decision_set(self):
        snapshot = _base_builder().build()
        assert snapshot.hire_decision == HireDecision.HIRE

    def test_level_set(self):
        snapshot = _base_builder().build()
        assert snapshot.level == InterviewLevel.STRONG

    def test_schema_version_default(self):
        snapshot = _base_builder().build()
        assert snapshot.schema_version == "1.0"

    def test_custom_schema_version(self):
        snapshot = _base_builder().with_schema_version("2.0").build()
        assert snapshot.schema_version == "2.0"

    def test_raw_score_none_by_default(self):
        snapshot = _base_builder().build()
        assert snapshot.raw_score is None

    def test_adjusted_score_none_by_default(self):
        snapshot = _base_builder().build()
        assert snapshot.adjusted_score is None

    def test_raw_and_adjusted_score_set(self):
        snapshot = _base_builder().with_raw_score(70.0).with_adjusted_score(74.0).build()
        assert snapshot.raw_score == 70.0
        assert snapshot.adjusted_score == 74.0

    def test_gating_not_triggered_no_reason(self):
        snapshot = _base_builder().with_gating(triggered=False).build()
        assert snapshot.gating_triggered is False
        assert snapshot.gating_reason is None

    def test_gating_triggered_with_reason(self):
        snapshot = _base_builder().with_gating(triggered=True, reason="Low technical score").build()
        assert snapshot.gating_triggered is True
        assert snapshot.gating_reason == "Low technical score"

    def test_confidence_set(self):
        snapshot = _base_builder().build()
        assert snapshot.confidence.base == pytest.approx(0.85)
        assert snapshot.confidence.final == pytest.approx(0.80)

    def test_accepts_list_of_dimensions(self):
        dims = list(_make_two_dimensions())
        snapshot = _base_builder(dimensions=None).with_scoring_dimensions(dims).build()
        assert len(snapshot.scoring_dimensions) == 2


# ---------------------------------------------------------------------------
# Derived dict generation (R-12)
# ---------------------------------------------------------------------------


class TestScoringSnapshotDerivedDicts:
    def test_dimension_scores_derived_from_dimensions(self):
        dims = _make_two_dimensions()
        snapshot = _base_builder(dims).build()
        assert snapshot.dimension_scores[PerformanceDimensionType.TECHNICAL_DEPTH.value] == pytest.approx(75.0)
        assert snapshot.dimension_scores[PerformanceDimensionType.PROBLEM_SOLVING.value] == pytest.approx(60.0)

    def test_dimension_signals_derived_from_dimensions(self):
        dims = _make_two_dimensions()
        snapshot = _base_builder(dims).build()
        assert snapshot.dimension_signals[PerformanceDimensionType.TECHNICAL_DEPTH.value] == pytest.approx(0.8)
        assert snapshot.dimension_signals[PerformanceDimensionType.PROBLEM_SOLVING.value] == pytest.approx(0.6)

    def test_weighted_breakdown_derived_from_dimensions(self):
        dims = _make_two_dimensions()
        snapshot = _base_builder(dims).build()
        assert snapshot.weighted_breakdown[PerformanceDimensionType.TECHNICAL_DEPTH.value] == pytest.approx(0.3)
        assert snapshot.weighted_breakdown[PerformanceDimensionType.PROBLEM_SOLVING.value] == pytest.approx(0.25)

    def test_dict_key_count_matches_dimension_count(self):
        dims = _make_two_dimensions()
        snapshot = _base_builder(dims).build()
        assert len(snapshot.dimension_scores) == 2
        assert len(snapshot.dimension_signals) == 2
        assert len(snapshot.weighted_breakdown) == 2

    def test_single_dimension_dicts_have_one_key(self):
        snapshot = _base_builder((_make_dimension(),)).build()
        assert len(snapshot.dimension_scores) == 1

    def test_all_five_dimensions_covered(self):
        dims = tuple(
            _make_dimension(dt, score=50.0 + i * 5, signal=0.5 + i * 0.05, weighted_contribution=0.1 + i * 0.02)
            for i, dt in enumerate(PerformanceDimensionType)
        )
        snapshot = _base_builder(dims).build()
        for dt in PerformanceDimensionType:
            assert dt.value in snapshot.dimension_scores
            assert dt.value in snapshot.dimension_signals
            assert dt.value in snapshot.weighted_breakdown


# ---------------------------------------------------------------------------
# Invariant enforcement
# ---------------------------------------------------------------------------


class TestScoringSnapshotInvariants:
    def test_v_ss_01_gating_triggered_without_reason_rejected(self):
        with pytest.raises(ValidationError, match="V-SS-01"):
            _base_builder().with_gating(triggered=True, reason=None).build()

    def test_v_ss_02_empty_dimensions_rejected_at_builder(self):
        with pytest.raises(ValueError):
            _base_builder().with_scoring_dimensions(()).build()

    def test_v_ss_02_empty_dimensions_rejected_at_model(self):
        dim = _make_dimension()
        with pytest.raises(ValidationError, match="V-SS-02"):
            ScoringSnapshot(
                overall_score=70.0,
                scoring_dimensions=(),
                dimension_scores={dim.dimension_type.value: 70.0},
                dimension_signals={dim.dimension_type.value: 0.7},
                weighted_breakdown={dim.dimension_type.value: 0.2},
                level=InterviewLevel.STRONG,
                hire_decision=HireDecision.HIRE,
                hiring_probability=75.0,
                percentile_rank=60.0,
                percentile_explanation="Above average.",
                decision_explanation={},
                gating_triggered=False,
                confidence=Confidence(base=0.8, final=0.8),
            )

    def test_r12_mismatched_dimension_scores_keys_rejected(self):
        dim = _make_dimension()
        with pytest.raises(ValidationError, match="R-12"):
            ScoringSnapshot(
                overall_score=70.0,
                scoring_dimensions=(dim,),
                dimension_scores={"wrong_key": 70.0},
                dimension_signals={dim.dimension_type.value: 0.7},
                weighted_breakdown={dim.dimension_type.value: 0.2},
                level=InterviewLevel.STRONG,
                hire_decision=HireDecision.HIRE,
                hiring_probability=75.0,
                percentile_rank=60.0,
                percentile_explanation="Above average.",
                decision_explanation={},
                gating_triggered=False,
                confidence=Confidence(base=0.8, final=0.8),
            )

    def test_r12_missing_key_in_dict_rejected(self):
        dims = _make_two_dimensions()
        dim1 = dims[0]
        with pytest.raises(ValidationError, match="R-12"):
            ScoringSnapshot(
                overall_score=70.0,
                scoring_dimensions=dims,
                # missing dims[1] key
                dimension_scores={dim1.dimension_type.value: dim1.score},
                dimension_signals={d.dimension_type.value: d.signal for d in dims},
                weighted_breakdown={d.dimension_type.value: d.weighted_contribution for d in dims},
                level=InterviewLevel.STRONG,
                hire_decision=HireDecision.HIRE,
                hiring_probability=75.0,
                percentile_rank=60.0,
                percentile_explanation="Above average.",
                decision_explanation={},
                gating_triggered=False,
                confidence=Confidence(base=0.8, final=0.8),
            )

    def test_overall_score_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _base_builder().with_overall_score(-1.0).build()

    def test_overall_score_above_hundred_rejected(self):
        with pytest.raises((ValidationError, ValueError)):
            _base_builder().with_overall_score(100.1).build()

    def test_hiring_probability_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _base_builder().with_hiring_probability(-0.1).build()

    def test_percentile_rank_above_hundred_rejected(self):
        with pytest.raises(ValidationError):
            _base_builder().with_percentile_rank(100.1).build()

    def test_empty_percentile_explanation_rejected(self):
        with pytest.raises(ValidationError):
            _base_builder().with_percentile_explanation("").build()

    def test_extra_field_on_snapshot_rejected(self):
        dim = _make_dimension()
        with pytest.raises(ValidationError):
            ScoringSnapshot(
                overall_score=70.0,
                scoring_dimensions=(dim,),
                dimension_scores={dim.dimension_type.value: 70.0},
                dimension_signals={dim.dimension_type.value: 0.7},
                weighted_breakdown={dim.dimension_type.value: 0.2},
                level=InterviewLevel.STRONG,
                hire_decision=HireDecision.HIRE,
                hiring_probability=75.0,
                percentile_rank=60.0,
                percentile_explanation="Above average.",
                decision_explanation={},
                gating_triggered=False,
                confidence=Confidence(base=0.8, final=0.8),
                unknown_field="value",
            )


# ---------------------------------------------------------------------------
# Builder ownership
# ---------------------------------------------------------------------------


class TestScoringSnapshotBuilderOwnership:
    def test_builder_missing_overall_score_raises(self):
        builder = (
            ScoringSnapshotBuilder()
            .with_scoring_dimensions((_make_dimension(),))
            .with_level(InterviewLevel.STRONG)
            .with_hire_decision(HireDecision.HIRE)
            .with_hiring_probability(75.0)
            .with_percentile_rank(60.0)
            .with_percentile_explanation("OK")
            .with_confidence(Confidence(base=0.8, final=0.8))
        )
        with pytest.raises(ValueError, match="overall_score"):
            builder.build()

    def test_builder_missing_confidence_raises(self):
        builder = (
            ScoringSnapshotBuilder()
            .with_overall_score(70.0)
            .with_scoring_dimensions((_make_dimension(),))
            .with_level(InterviewLevel.STRONG)
            .with_hire_decision(HireDecision.HIRE)
            .with_hiring_probability(75.0)
            .with_percentile_rank(60.0)
            .with_percentile_explanation("OK")
        )
        with pytest.raises(ValueError, match="confidence"):
            builder.build()

    def test_builder_missing_level_raises(self):
        builder = (
            ScoringSnapshotBuilder()
            .with_overall_score(70.0)
            .with_scoring_dimensions((_make_dimension(),))
            .with_hire_decision(HireDecision.HIRE)
            .with_hiring_probability(75.0)
            .with_percentile_rank(60.0)
            .with_percentile_explanation("OK")
            .with_confidence(Confidence(base=0.8, final=0.8))
        )
        with pytest.raises(ValueError, match="level"):
            builder.build()

    def test_builder_is_reusable(self):
        builder = _base_builder()
        s1 = builder.build()
        s2 = builder.build()
        assert s1 == s2

    def test_each_build_call_produces_independent_instance(self):
        builder = _base_builder()
        s1 = builder.build()
        s2 = builder.build()
        assert s1 is not s2


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


class TestScoringSnapshotImmutability:
    def test_overall_score_assignment_raises(self):
        snapshot = _base_builder().build()
        with pytest.raises((TypeError, ValidationError)):
            snapshot.overall_score = 50.0  # type: ignore[misc]

    def test_hire_decision_assignment_raises(self):
        snapshot = _base_builder().build()
        with pytest.raises((TypeError, ValidationError)):
            snapshot.hire_decision = HireDecision.NO_HIRE  # type: ignore[misc]

    def test_scoring_dimensions_assignment_raises(self):
        snapshot = _base_builder().build()
        with pytest.raises((TypeError, ValidationError)):
            snapshot.scoring_dimensions = ()  # type: ignore[misc]

    def test_dimension_scores_assignment_raises(self):
        snapshot = _base_builder().build()
        with pytest.raises((TypeError, ValidationError)):
            snapshot.dimension_scores = {}  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


class TestScoringSnapshotSerialization:
    def test_model_dump_contains_all_top_level_keys(self):
        snapshot = _base_builder().build()
        data = snapshot.model_dump()
        expected_keys = {
            "overall_score", "raw_score", "adjusted_score",
            "scoring_dimensions", "dimension_scores", "dimension_signals",
            "weighted_breakdown", "level", "hire_decision",
            "hiring_probability", "percentile_rank", "percentile_explanation",
            "decision_explanation", "gating_triggered", "gating_reason",
            "confidence", "schema_version",
        }
        assert expected_keys.issubset(set(data.keys()))

    def test_round_trip_preserves_all_fields(self):
        snapshot = _base_builder(_make_two_dimensions()).build()
        restored = ScoringSnapshot.model_validate(snapshot.model_dump())
        assert restored == snapshot

    def test_schema_version_in_dump(self):
        snapshot = _base_builder().build()
        assert snapshot.model_dump()["schema_version"] == "1.0"

    def test_round_trip_with_gating(self):
        snapshot = _base_builder().with_gating(triggered=True, reason="Low score").build()
        restored = ScoringSnapshot.model_validate(snapshot.model_dump())
        assert restored.gating_triggered is True
        assert restored.gating_reason == "Low score"


# ---------------------------------------------------------------------------
# Equality
# ---------------------------------------------------------------------------


class TestScoringSnapshotEquality:
    def test_equal_snapshots(self):
        a = _base_builder().build()
        b = _base_builder().build()
        assert a == b

    def test_different_overall_score_not_equal(self):
        a = _base_builder().with_overall_score(70.0).build()
        b = _base_builder().with_overall_score(80.0).build()
        assert a != b

    def test_different_hire_decision_not_equal(self):
        a = _base_builder().with_hire_decision(HireDecision.HIRE).build()
        b = _base_builder().with_hire_decision(HireDecision.NO_HIRE).build()
        assert a != b

    def test_different_dimensions_not_equal(self):
        dim_a = (_make_dimension(score=70.0),)
        dim_b = (_make_dimension(score=80.0),)
        a = _base_builder(dim_a).build()
        b = _base_builder(dim_b).build()
        assert a != b
