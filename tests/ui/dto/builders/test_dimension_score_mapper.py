# tests/ui/dto/builders/test_dimension_score_mapper.py

from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType
from app.ui.dto.builders.dimension_score_mapper import DimensionScoreMapper


def _enum_scores():
    return {
        PerformanceDimensionType.TECHNICAL_DEPTH: 75.0,
        PerformanceDimensionType.PROBLEM_SOLVING: 60.0,
    }


def _enum_breakdown():
    return {
        PerformanceDimensionType.TECHNICAL_DEPTH: 40.0,
        PerformanceDimensionType.PROBLEM_SOLVING: 30.0,
    }


def _str_scores():
    return {
        "technical_depth": 75.0,
        "problem_solving": 60.0,
    }


def _str_breakdown():
    return {
        "technical_depth": 40.0,
        "problem_solving": 30.0,
    }


class TestDimensionScoreMapper:

    def test_enum_keys_produce_correct_labels(self):
        mapper = DimensionScoreMapper()
        dtos = mapper.map(_enum_scores())
        names = {d.name for d in dtos}
        assert "Technical Depth" in names
        assert "Problem Solving" in names

    def test_str_keys_produce_correct_labels(self):
        mapper = DimensionScoreMapper()
        dtos = mapper.map(_str_scores())
        names = {d.name for d in dtos}
        assert "Technical Depth" in names
        assert "Problem Solving" in names

    def test_enum_keys_with_enum_breakdown_extracts_contribution(self):
        mapper = DimensionScoreMapper()
        dtos = mapper.map(_enum_scores(), _enum_breakdown())
        by_name = {d.name: d for d in dtos}
        assert by_name["Technical Depth"].contribution == 40.0
        assert by_name["Problem Solving"].contribution == 30.0

    def test_str_keys_with_str_breakdown_extracts_contribution(self):
        mapper = DimensionScoreMapper()
        dtos = mapper.map(_str_scores(), _str_breakdown())
        by_name = {d.name: d for d in dtos}
        assert by_name["Technical Depth"].contribution == 40.0
        assert by_name["Problem Solving"].contribution == 30.0

    def test_weight_computed_from_contribution_and_score(self):
        mapper = DimensionScoreMapper()
        dtos = mapper.map(_str_scores(), _str_breakdown())
        by_name = {d.name: d for d in dtos}
        expected_weight = round(40.0 / 75.0, 2)
        assert by_name["Technical Depth"].weight == expected_weight

    def test_no_breakdown_yields_zero_weight_and_contribution(self):
        mapper = DimensionScoreMapper()
        dtos = mapper.map(_str_scores(), None)
        for d in dtos:
            assert d.weight == 0.0
            assert d.contribution == 0.0

    def test_empty_scores_returns_empty_list(self):
        mapper = DimensionScoreMapper()
        assert mapper.map({}) == []

    def test_all_dtos_are_evaluated(self):
        mapper = DimensionScoreMapper()
        dtos = mapper.map(_str_scores())
        assert all(d.is_evaluated for d in dtos)

    def test_status_strong_above_threshold(self):
        from infrastructure.config.evaluation import REPORT_DIMENSION_STRONG_THRESHOLD
        mapper = DimensionScoreMapper()
        dtos = mapper.map({"problem_solving": REPORT_DIMENSION_STRONG_THRESHOLD + 1.0})
        assert dtos[0].status == "strong"

    def test_status_weak_below_threshold(self):
        from infrastructure.config.evaluation import REPORT_DIMENSION_MODERATE_THRESHOLD
        mapper = DimensionScoreMapper()
        dtos = mapper.map({"problem_solving": REPORT_DIMENSION_MODERATE_THRESHOLD - 1.0})
        assert dtos[0].status == "weak"
