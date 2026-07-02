# tests/domain/profile/conftest.py
"""Shared fixtures for CandidateProfile runtime tests."""

import pytest

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from domain.profile.candidate_profile_builder import CandidateProfileBuilder


def _trace(
    average_score: float,
    evidence_count: int,
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


@pytest.fixture()
def empty_profile() -> CandidateProfile:
    return CandidateProfileBuilder().build()


@pytest.fixture()
def single_dimension_profile() -> CandidateProfile:
    return (
        CandidateProfileBuilder()
        .with_dimension(ProfileDimension.TECHNICAL_DEPTH, _trace(70.0, 3, Trend.IMPROVING))
        .with_questions_answered(3)
        .with_areas_covered(["algorithms"])
        .with_last_updated_at(2)
        .build()
    )


@pytest.fixture()
def full_profile() -> CandidateProfile:
    return (
        CandidateProfileBuilder()
        .with_dimension(ProfileDimension.TECHNICAL_DEPTH, _trace(80.0, 5, Trend.IMPROVING))
        .with_dimension(ProfileDimension.PROBLEM_SOLVING, _trace(60.0, 4, Trend.STABLE))
        .with_dimension(ProfileDimension.COMMUNICATION, _trace(50.0, 3, Trend.DECLINING))
        .with_dimension(ProfileDimension.SYSTEM_DESIGN, _trace(70.0, 4, Trend.STABLE))
        .with_dimension(ProfileDimension.ENGINEERING_JUDGMENT, _trace(40.0, 2, Trend.INSUFFICIENT_DATA))
        .with_questions_answered(10)
        .with_areas_covered(["algorithms", "system design", "communication"])
        .with_last_updated_at(9)
        .build()
    )


@pytest.fixture()
def improved_profile(full_profile: CandidateProfile) -> CandidateProfile:
    return (
        CandidateProfileBuilder.from_profile(full_profile)
        .with_dimension(ProfileDimension.TECHNICAL_DEPTH, _trace(90.0, 7, Trend.IMPROVING))
        .with_dimension(ProfileDimension.PROBLEM_SOLVING, _trace(75.0, 6, Trend.IMPROVING))
        .with_questions_answered(14)
        .build()
    )
