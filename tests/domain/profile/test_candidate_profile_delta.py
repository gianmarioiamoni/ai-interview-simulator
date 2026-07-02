# tests/domain/profile/test_candidate_profile_delta.py
"""Tests for CandidateProfileDelta."""

import pytest

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from domain.profile.candidate_profile_delta import CandidateProfileDelta, DimensionDelta


class TestDeltaContract:
    def test_returns_delta_instance(self, full_profile: CandidateProfile) -> None:
        delta = CandidateProfileDelta.compute(full_profile, full_profile)
        assert isinstance(delta, CandidateProfileDelta)

    def test_all_five_dimensions_present(self, full_profile: CandidateProfile) -> None:
        delta = CandidateProfileDelta.compute(full_profile, full_profile)
        dims = {d.dimension for d in delta.dimension_deltas}
        assert dims == set(ProfileDimension)

    def test_identical_profiles_no_change(self, full_profile: CandidateProfile) -> None:
        delta = CandidateProfileDelta.compute(full_profile, full_profile)
        assert not delta.has_any_change


class TestDeltaBehavior:
    def test_score_delta_positive_on_improvement(
        self, full_profile: CandidateProfile, improved_profile: CandidateProfile
    ) -> None:
        delta = CandidateProfileDelta.compute(full_profile, improved_profile)
        td = next(d for d in delta.dimension_deltas if d.dimension == ProfileDimension.TECHNICAL_DEPTH)
        assert td.score_delta > 0.0

    def test_questions_delta_computed(
        self, full_profile: CandidateProfile, improved_profile: CandidateProfile
    ) -> None:
        delta = CandidateProfileDelta.compute(full_profile, improved_profile)
        assert delta.questions_delta == improved_profile.questions_answered - full_profile.questions_answered

    def test_new_areas_detected(self, full_profile: CandidateProfile) -> None:
        from domain.profile.candidate_profile_builder import CandidateProfileBuilder
        updated = CandidateProfileBuilder.from_profile(full_profile).with_areas_covered(
            full_profile.areas_covered + ["databases"]
        ).build()
        delta = CandidateProfileDelta.compute(full_profile, updated)
        assert "databases" in delta.new_areas_covered

    def test_removed_areas_detected(self, full_profile: CandidateProfile) -> None:
        from domain.profile.candidate_profile_builder import CandidateProfileBuilder
        reduced = CandidateProfileBuilder.from_profile(full_profile).with_areas_covered([]).build()
        delta = CandidateProfileDelta.compute(full_profile, reduced)
        assert set(delta.removed_areas) == set(full_profile.areas_covered)

    def test_trend_change_detected(
        self, full_profile: CandidateProfile, improved_profile: CandidateProfile
    ) -> None:
        delta = CandidateProfileDelta.compute(full_profile, improved_profile)
        ps_delta = next(d for d in delta.dimension_deltas if d.dimension == ProfileDimension.PROBLEM_SOLVING)
        assert ps_delta.trend_before == Trend.STABLE
        assert ps_delta.trend_after == Trend.IMPROVING
        assert ps_delta.trend_changed

    def test_has_any_change_true_on_improvement(
        self, full_profile: CandidateProfile, improved_profile: CandidateProfile
    ) -> None:
        delta = CandidateProfileDelta.compute(full_profile, improved_profile)
        assert delta.has_any_change

    def test_evidence_delta_positive(
        self, full_profile: CandidateProfile, improved_profile: CandidateProfile
    ) -> None:
        delta = CandidateProfileDelta.compute(full_profile, improved_profile)
        td = next(d for d in delta.dimension_deltas if d.dimension == ProfileDimension.TECHNICAL_DEPTH)
        assert td.evidence_delta > 0
