# tests/domain/profile/test_profile_integration.py
"""Integration tests: Builder → Statistics → Delta → Comparison → Summary pipeline."""

import pytest

from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from domain.profile.candidate_profile_builder import CandidateProfileBuilder
from domain.profile.candidate_profile_comparison import (
    CandidateProfileComparison,
    ComparisonVerdict,
)
from domain.profile.candidate_profile_delta import CandidateProfileDelta
from domain.profile.candidate_profile_statistics import CandidateProfileStatistics
from domain.profile.candidate_profile_summary import (
    CandidateProfileSummary,
    ProfileMaturityLevel,
)
from tests.domain.profile.profile_test_helpers import (
    candidate_profile_with_dimension_scores,
)


def _trace(avg: float, count: int, trend: Trend = Trend.STABLE) -> DimensionTrace:
    return DimensionTrace(
        average_score=avg,
        last_score=avg,
        trend=trend,
        confidence=min(count / 10.0, 1.0),
        evidence_count=count,
        last_updated_question=count - 1,
    )


class TestBuilderToPipelineIntegration:
    def test_builder_produces_profile_consumed_by_statistics(self) -> None:
        profile = candidate_profile_with_dimension_scores(
            {ProfileDimension.TECHNICAL_DEPTH: _trace(75.0, 5)},
            questions_answered=5,
        )
        stats = CandidateProfileStatistics.compute(profile)
        assert stats.assessed_dimension_count == 1
        assert stats.dominant_dimension == ProfileDimension.TECHNICAL_DEPTH

    def test_delta_then_comparison_consistent(self) -> None:
        before = candidate_profile_with_dimension_scores(
            {ProfileDimension.TECHNICAL_DEPTH: _trace(60.0, 3)},
            questions_answered=3,
        )
        after = candidate_profile_with_dimension_scores(
            {ProfileDimension.TECHNICAL_DEPTH: _trace(80.0, 6, Trend.IMPROVING)},
            questions_answered=6,
        )

        delta = CandidateProfileDelta.compute(before, after)
        comparison = CandidateProfileComparison.compare(before, after)

        assert delta.has_any_change
        assert comparison.verdict == ComparisonVerdict.IMPROVED
        assert comparison.delta.questions_delta == delta.questions_delta

    def test_summary_reflects_statistics(self) -> None:
        profile = candidate_profile_with_dimension_scores(
            {
                ProfileDimension.TECHNICAL_DEPTH: _trace(85.0, 6, Trend.IMPROVING),
                ProfileDimension.PROBLEM_SOLVING: _trace(65.0, 4, Trend.STABLE),
                ProfileDimension.COMMUNICATION: _trace(45.0, 3, Trend.DECLINING),
            },
            questions_answered=8,
            areas_covered=["algo", "design"],
        )
        summary = CandidateProfileSummary.summarize(profile)
        stats = CandidateProfileStatistics.compute(profile)

        assert summary.assessed_count == stats.assessed_dimension_count
        assert summary.dominant_dimension == stats.dominant_dimension
        assert summary.weakest_dimension == stats.weakest_dimension
        assert summary.maturity == ProfileMaturityLevel.DEVELOPING

    def test_from_profile_round_trip_identity(self) -> None:
        original = (
            CandidateProfileBuilder()
            .with_questions_answered(4)
            .with_areas_covered(["cloud"])
            .with_last_updated_at(3)
            .build()
        )
        clone = CandidateProfileBuilder.from_profile(original).build()
        assert clone == original

    def test_empty_to_full_evolution(self) -> None:
        empty = CandidateProfileBuilder().build()
        full = candidate_profile_with_dimension_scores(
            {
                ProfileDimension.TECHNICAL_DEPTH: _trace(70.0, 5, Trend.IMPROVING),
                ProfileDimension.PROBLEM_SOLVING: _trace(55.0, 4, Trend.STABLE),
                ProfileDimension.COMMUNICATION: _trace(60.0, 3, Trend.STABLE),
                ProfileDimension.SYSTEM_DESIGN: _trace(65.0, 4, Trend.STABLE),
                ProfileDimension.ENGINEERING_JUDGMENT: _trace(50.0, 2),
            },
            questions_answered=10,
            areas_covered=["algorithms", "design"],
        )

        delta = CandidateProfileDelta.compute(empty, full)
        comparison = CandidateProfileComparison.compare(empty, full)
        summary = CandidateProfileSummary.summarize(full)

        assert delta.has_any_change
        assert delta.questions_delta == 10
        assert comparison.verdict == ComparisonVerdict.IMPROVED
        assert summary.maturity == ProfileMaturityLevel.COMPLETE
        assert summary.is_data_sufficient
