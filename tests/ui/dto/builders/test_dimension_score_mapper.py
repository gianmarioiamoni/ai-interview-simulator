# tests/ui/dto/builders/test_dimension_score_mapper.py
# EPIC-V13-05 Phase 9 — DimensionScoreMapper accepts tuple[ScoringDimension, ...] (R-16).
# Three-parameter dict signature removed.

from domain.contracts.report.scoring_dimension import ScoringDimension
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType
from app.ui.dto.builders.dimension_score_mapper import DimensionScoreMapper


def _make_dim(
    dim_type: PerformanceDimensionType = PerformanceDimensionType.TECHNICAL_DEPTH,
    score: float = 75.0,
    signal: float = 0.8,
    weighted_contribution: float = 0.4,
    justification: str = "Good performance.",
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


class TestDimensionScoreMapper:

    def test_single_dimension_produces_correct_label(self):
        dtos = DimensionScoreMapper().map((_make_dim(),))
        assert len(dtos) == 1
        assert dtos[0].name == "Technical Depth"

    def test_multiple_dimensions_produce_correct_labels(self):
        dims = (
            _make_dim(PerformanceDimensionType.TECHNICAL_DEPTH),
            _make_dim(PerformanceDimensionType.PROBLEM_SOLVING, score=60.0),
        )
        dtos = DimensionScoreMapper().map(dims)
        names = {d.name for d in dtos}
        assert "Technical Depth" in names
        assert "Problem Solving" in names

    def test_contribution_from_scoring_dimension(self):
        dim = _make_dim(weighted_contribution=0.4)
        dtos = DimensionScoreMapper().map((dim,))
        assert dtos[0].contribution == 0.4

    def test_justification_from_scoring_dimension(self):
        dim = _make_dim(justification="Excellent reasoning.")
        dtos = DimensionScoreMapper().map((dim,))
        assert dtos[0].justification == "Excellent reasoning."

    def test_status_taken_from_scoring_dimension_level(self):
        dim = _make_dim(level="weak")
        dtos = DimensionScoreMapper().map((dim,))
        assert dtos[0].status == "weak"

    def test_weight_computed_from_contribution_and_score(self):
        dim = _make_dim(score=75.0, weighted_contribution=0.4)
        dtos = DimensionScoreMapper().map((dim,))
        expected_weight = round(0.4 / 75.0, 2)
        assert dtos[0].weight == expected_weight

    def test_empty_tuple_returns_empty_list(self):
        assert DimensionScoreMapper().map(()) == []

    def test_all_dtos_are_evaluated(self):
        dtos = DimensionScoreMapper().map((_make_dim(),))
        assert all(d.is_evaluated for d in dtos)

    def test_max_score_is_100(self):
        dtos = DimensionScoreMapper().map((_make_dim(),))
        assert dtos[0].max_score == 100.0
