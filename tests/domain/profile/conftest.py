# tests/domain/profile/conftest.py
"""Shared fixtures for CandidateProfile runtime tests."""

import pytest

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from domain.profile.candidate_profile_builder import CandidateProfileBuilder
from tests.domain.profile.profile_test_helpers import (
    candidate_profile_with_dimension_scores,
)


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
    return candidate_profile_with_dimension_scores(
        {ProfileDimension.TECHNICAL_DEPTH: _trace(70.0, 3, Trend.IMPROVING)},
        questions_answered=3,
        areas_covered=["algorithms"],
        last_updated_at_question_index=2,
    )


@pytest.fixture()
def full_profile() -> CandidateProfile:
    return candidate_profile_with_dimension_scores(
        {
            ProfileDimension.TECHNICAL_DEPTH: _trace(80.0, 5, Trend.IMPROVING),
            ProfileDimension.PROBLEM_SOLVING: _trace(60.0, 4, Trend.STABLE),
            ProfileDimension.COMMUNICATION: _trace(50.0, 3, Trend.DECLINING),
            ProfileDimension.SYSTEM_DESIGN: _trace(70.0, 4, Trend.STABLE),
            ProfileDimension.ENGINEERING_JUDGMENT: _trace(
                40.0, 2, Trend.INSUFFICIENT_DATA
            ),
        },
        questions_answered=10,
        areas_covered=["algorithms", "system design", "communication"],
        last_updated_at_question_index=9,
    )


@pytest.fixture()
def improved_profile(full_profile: CandidateProfile) -> CandidateProfile:
    scores = dict(full_profile.dimension_scores)
    scores[ProfileDimension.TECHNICAL_DEPTH] = _trace(90.0, 7, Trend.IMPROVING)
    scores[ProfileDimension.PROBLEM_SOLVING] = _trace(75.0, 6, Trend.IMPROVING)
    return candidate_profile_with_dimension_scores(
        scores,
        questions_answered=14,
        areas_covered=list(full_profile.areas_covered),
        last_updated_at_question_index=full_profile.last_updated_at_question_index,
        signals=dict(full_profile.signals),
    )
