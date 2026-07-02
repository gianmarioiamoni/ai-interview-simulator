# tests/domain/profile/test_candidate_profile_summary.py
"""Tests for CandidateProfileSummary."""

import pytest

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from domain.profile.candidate_profile_summary import (
    CandidateProfileSummary,
    ProfileMaturityLevel,
    ProfileSummaryResult,
    Scoreband,
)


class TestSummaryContract:
    def test_returns_summary_result(self, empty_profile: CandidateProfile) -> None:
        result = CandidateProfileSummary.summarize(empty_profile)
        assert isinstance(result, ProfileSummaryResult)

    def test_all_five_dimensions_in_entries(self, empty_profile: CandidateProfile) -> None:
        result = CandidateProfileSummary.summarize(empty_profile)
        dims = {e.dimension for e in result.dimension_entries}
        assert dims == set(ProfileDimension)


class TestSummaryBehavior:
    def test_empty_profile_is_empty_maturity(self, empty_profile: CandidateProfile) -> None:
        result = CandidateProfileSummary.summarize(empty_profile)
        assert result.maturity == ProfileMaturityLevel.EMPTY

    def test_single_dimension_is_early_maturity(self, single_dimension_profile: CandidateProfile) -> None:
        result = CandidateProfileSummary.summarize(single_dimension_profile)
        assert result.maturity == ProfileMaturityLevel.EARLY

    def test_full_profile_is_complete_maturity(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileSummary.summarize(full_profile)
        assert result.maturity == ProfileMaturityLevel.COMPLETE

    def test_scoreband_very_high_for_score_above_80(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileSummary.summarize(full_profile)
        td = next(e for e in result.dimension_entries if e.dimension == ProfileDimension.TECHNICAL_DEPTH)
        assert td.scoreband == Scoreband.VERY_HIGH

    def test_scoreband_low_for_score_40(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileSummary.summarize(full_profile)
        ej = next(e for e in result.dimension_entries if e.dimension == ProfileDimension.ENGINEERING_JUDGMENT)
        assert ej.scoreband == Scoreband.LOW

    def test_is_data_sufficient_false_when_few_dimensions(
        self, single_dimension_profile: CandidateProfile
    ) -> None:
        result = CandidateProfileSummary.summarize(single_dimension_profile)
        assert not result.is_data_sufficient

    def test_is_data_sufficient_true_for_full_profile(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileSummary.summarize(full_profile)
        assert result.is_data_sufficient

    def test_has_improving_trend_detected(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileSummary.summarize(full_profile)
        assert result.has_improving_trend

    def test_has_declining_trend_detected(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileSummary.summarize(full_profile)
        assert result.has_declining_trend

    def test_dominant_dimension_is_highest_score(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileSummary.summarize(full_profile)
        assert result.dominant_dimension == ProfileDimension.TECHNICAL_DEPTH

    def test_weakest_dimension_is_lowest_score(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileSummary.summarize(full_profile)
        assert result.weakest_dimension == ProfileDimension.ENGINEERING_JUDGMENT

    def test_areas_covered_preserved(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileSummary.summarize(full_profile)
        assert set(result.areas_covered) == set(full_profile.areas_covered)

    def test_questions_answered_preserved(self, full_profile: CandidateProfile) -> None:
        result = CandidateProfileSummary.summarize(full_profile)
        assert result.questions_answered == full_profile.questions_answered

    def test_unassessed_dimensions_are_not_assessed(self, single_dimension_profile: CandidateProfile) -> None:
        result = CandidateProfileSummary.summarize(single_dimension_profile)
        unassessed = [e for e in result.dimension_entries if not e.is_assessed]
        assert len(unassessed) == 4
