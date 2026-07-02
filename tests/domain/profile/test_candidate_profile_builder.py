# tests/domain/profile/test_candidate_profile_builder.py
"""Tests for CandidateProfileBuilder — contract, behavior, architecture."""

import pytest
from pydantic import ValidationError

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.profile_signal import ProfileSignal
from domain.contracts.reasoning.signal_trace import SignalTrace
from domain.contracts.reasoning.trend import Trend
from domain.profile.candidate_profile_builder import CandidateProfileBuilder


def _trace(avg: float = 50.0, count: int = 1) -> DimensionTrace:
    return DimensionTrace(
        average_score=avg,
        last_score=avg,
        trend=Trend.STABLE,
        confidence=0.5,
        evidence_count=count,
        last_updated_question=0,
    )


class TestBuilderContract:
    def test_build_returns_candidate_profile(self) -> None:
        profile = CandidateProfileBuilder().build()
        assert isinstance(profile, CandidateProfile)

    def test_build_returns_frozen_object(self) -> None:
        profile = CandidateProfileBuilder().build()
        with pytest.raises((ValidationError, TypeError)):
            profile.questions_answered = 5  # type: ignore[misc]

    def test_empty_build_has_defaults(self) -> None:
        profile = CandidateProfileBuilder().build()
        assert profile.questions_answered == 0
        assert profile.areas_covered == []
        assert profile.dimension_scores == {}
        assert profile.signals == {}
        assert profile.last_updated_at_question_index == -1

    def test_extra_fields_forbidden(self) -> None:
        """CandidateProfile model_config extra=forbid must hold."""
        with pytest.raises(ValidationError):
            CandidateProfile(unknown_field="x")  # type: ignore[call-arg]


class TestBuilderBehavior:
    def test_with_dimension(self) -> None:
        t = _trace(70.0, 3)
        profile = CandidateProfileBuilder().with_dimension(ProfileDimension.TECHNICAL_DEPTH, t).build()
        assert profile.dimension_scores[ProfileDimension.TECHNICAL_DEPTH] == t

    def test_with_dimensions_replaces_all(self) -> None:
        dims = {
            ProfileDimension.TECHNICAL_DEPTH: _trace(70.0),
            ProfileDimension.PROBLEM_SOLVING: _trace(55.0),
        }
        profile = CandidateProfileBuilder().with_dimensions(dims).build()
        assert set(profile.dimension_scores.keys()) == {
            ProfileDimension.TECHNICAL_DEPTH,
            ProfileDimension.PROBLEM_SOLVING,
        }

    def test_with_questions_answered(self) -> None:
        profile = CandidateProfileBuilder().with_questions_answered(7).build()
        assert profile.questions_answered == 7

    def test_with_questions_answered_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            CandidateProfileBuilder().with_questions_answered(-1)

    def test_with_areas_covered(self) -> None:
        profile = CandidateProfileBuilder().with_areas_covered(["a", "b"]).build()
        assert profile.areas_covered == ["a", "b"]

    def test_with_last_updated_at(self) -> None:
        profile = CandidateProfileBuilder().with_last_updated_at(5).build()
        assert profile.last_updated_at_question_index == 5

    def test_fluent_chaining_returns_self(self) -> None:
        builder = CandidateProfileBuilder()
        result = builder.with_questions_answered(1).with_areas_covered(["x"]).with_last_updated_at(0)
        assert result is builder

    def test_with_signal(self) -> None:
        st = SignalTrace()
        profile = CandidateProfileBuilder().with_signal(ProfileSignal.CONFIDENCE, st).build()
        assert profile.signals[ProfileSignal.CONFIDENCE] == st


class TestBuilderFromProfile:
    def test_from_profile_copies_all_fields(self, full_profile: CandidateProfile) -> None:
        rebuilt = CandidateProfileBuilder.from_profile(full_profile).build()
        assert rebuilt == full_profile

    def test_from_profile_mutations_do_not_affect_original(self, full_profile: CandidateProfile) -> None:
        builder = CandidateProfileBuilder.from_profile(full_profile)
        builder.with_questions_answered(999)
        assert full_profile.questions_answered != 999

    def test_from_profile_allows_override(self, full_profile: CandidateProfile) -> None:
        new_trace = _trace(99.0, 10)
        updated = (
            CandidateProfileBuilder.from_profile(full_profile)
            .with_dimension(ProfileDimension.TECHNICAL_DEPTH, new_trace)
            .build()
        )
        assert updated.dimension_scores[ProfileDimension.TECHNICAL_DEPTH].average_score == 99.0
        assert updated.questions_answered == full_profile.questions_answered


class TestBuilderArchitecture:
    def test_build_always_returns_new_instance(self) -> None:
        builder = CandidateProfileBuilder()
        p1 = builder.build()
        p2 = builder.build()
        assert p1 is not p2

    def test_multiple_builds_are_equal(self) -> None:
        builder = CandidateProfileBuilder().with_questions_answered(3)
        assert builder.build() == builder.build()
