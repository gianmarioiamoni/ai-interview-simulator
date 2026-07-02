# tests/domain/profile/test_candidate_profile_statistics.py
"""Tests for CandidateProfileStatistics."""

import pytest

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from domain.profile.candidate_profile_statistics import (
    CandidateProfileStatistics,
    ProfileStatisticsResult,
)


class TestStatisticsContract:
    def test_returns_statistics_result(self, empty_profile: CandidateProfile) -> None:
        result = CandidateProfileStatistics.compute(empty_profile)
        assert isinstance(result, ProfileStatisticsResult)

    def test_all_five_dimensions_always_present(self, empty_profile: CandidateProfile) -> None:
        result = CandidateProfileStatistics.compute(empty_profile)
        dims = {s.dimension for s in result.dimension_stats}
        assert dims == set(ProfileDimension)

    def test_coverage_ratio_is_between_0_and_1(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileStatistics.compute(full_profile)
        assert 0.0 <= result.coverage_ratio <= 1.0


class TestStatisticsBehavior:
    def test_empty_profile_has_zero_overall_score(self, empty_profile: CandidateProfile) -> None:
        result = CandidateProfileStatistics.compute(empty_profile)
        assert result.overall_average_score == 0.0
        assert result.assessed_dimension_count == 0
        assert result.total_evidence_count == 0

    def test_full_profile_assessed_count(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileStatistics.compute(full_profile)
        assert result.assessed_dimension_count == 5

    def test_dominant_dimension_has_highest_score(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileStatistics.compute(full_profile)
        assert result.dominant_dimension == ProfileDimension.TECHNICAL_DEPTH

    def test_weakest_dimension_has_lowest_score(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileStatistics.compute(full_profile)
        assert result.weakest_dimension == ProfileDimension.ENGINEERING_JUDGMENT

    def test_improving_dimensions_from_trend(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileStatistics.compute(full_profile)
        assert ProfileDimension.TECHNICAL_DEPTH in result.improving_dimensions

    def test_declining_dimensions_from_trend(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileStatistics.compute(full_profile)
        assert ProfileDimension.COMMUNICATION in result.declining_dimensions

    def test_single_dimension_coverage_ratio(self, single_dimension_profile: CandidateProfile) -> None:
        result = CandidateProfileStatistics.compute(single_dimension_profile)
        assert result.coverage_ratio == pytest.approx(1 / 5, rel=1e-3)

    def test_overall_average_reflects_all_scored_dimensions(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileStatistics.compute(full_profile)
        expected = (80.0 + 60.0 + 50.0 + 70.0 + 40.0) / 5
        assert result.overall_average_score == pytest.approx(expected, rel=1e-3)

    def test_total_evidence_count(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileStatistics.compute(full_profile)
        assert result.total_evidence_count == 5 + 4 + 3 + 4 + 2
