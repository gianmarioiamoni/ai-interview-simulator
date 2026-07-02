# tests/domain/profile/test_candidate_profile_comparison.py
"""Tests for CandidateProfileComparison."""

import pytest

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.profile.candidate_profile_comparison import (
    CandidateProfileComparison,
    ComparisonVerdict,
    ProfileComparisonResult,
)
from domain.profile.candidate_profile_delta import CandidateProfileDelta


class TestComparisonContract:
    def test_returns_result_instance(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileComparison.compare(full_profile, full_profile)
        assert isinstance(result, ProfileComparisonResult)

    def test_result_embeds_delta(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileComparison.compare(full_profile, full_profile)
        assert isinstance(result.delta, CandidateProfileDelta)

    def test_all_five_dimensions_compared(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileComparison.compare(full_profile, full_profile)
        dims = {c.dimension for c in result.dimension_comparisons}
        assert dims == set(ProfileDimension)


class TestComparisonBehavior:
    def test_identical_profiles_are_identical(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileComparison.compare(full_profile, full_profile)
        assert result.are_identical
        assert result.verdict == ComparisonVerdict.IDENTICAL

    def test_improved_right_gives_improved_verdict(
        self, full_profile: CandidateProfile, improved_profile: CandidateProfile
    ) -> None:
        result = CandidateProfileComparison.compare(full_profile, improved_profile)
        assert result.verdict == ComparisonVerdict.IMPROVED

    def test_improved_dimensions_populated(
        self, full_profile: CandidateProfile, improved_profile: CandidateProfile
    ) -> None:
        result = CandidateProfileComparison.compare(full_profile, improved_profile)
        assert ProfileDimension.TECHNICAL_DEPTH in result.improved_dimensions

    def test_regressed_right_gives_regressed_verdict(
        self, full_profile: CandidateProfile, improved_profile: CandidateProfile
    ) -> None:
        result = CandidateProfileComparison.compare(improved_profile, full_profile)
        assert result.verdict == ComparisonVerdict.REGRESSED

    def test_regressed_dimensions_populated(
        self, full_profile: CandidateProfile, improved_profile: CandidateProfile
    ) -> None:
        result = CandidateProfileComparison.compare(improved_profile, full_profile)
        assert ProfileDimension.TECHNICAL_DEPTH in result.regressed_dimensions

    def test_empty_profiles_give_insufficient_data(self, empty_profile: CandidateProfile) -> None:
        result = CandidateProfileComparison.compare(empty_profile, empty_profile)
        assert result.verdict == ComparisonVerdict.INSUFFICIENT_DATA

    def test_overall_score_diff_positive_on_improvement(
        self, full_profile: CandidateProfile, improved_profile: CandidateProfile
    ) -> None:
        result = CandidateProfileComparison.compare(full_profile, improved_profile)
        assert result.overall_score_diff > 0.0

    def test_score_diff_negative_on_regression(
        self, full_profile: CandidateProfile, improved_profile: CandidateProfile
    ) -> None:
        result = CandidateProfileComparison.compare(improved_profile, full_profile)
        assert result.overall_score_diff < 0.0

    def test_are_identical_false_when_changed(
        self, full_profile: CandidateProfile, improved_profile: CandidateProfile
    ) -> None:
        result = CandidateProfileComparison.compare(full_profile, improved_profile)
        assert not result.are_identical
