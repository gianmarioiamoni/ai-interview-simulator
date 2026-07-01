# tests/services/interview_reasoner/profile/test_dominant_dimension_calculator.py
"""Tests for DominantDimensionCalculator (M2-6C)."""

import pytest

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from services.interview_reasoner.profile.dominant_dimension_calculator import (
    DominantDimensionCalculator,
)

from tests.services.interview_reasoner.profile.conftest import empty_profile, mk_trace

_calc = DominantDimensionCalculator()
TD = ProfileDimension.TECHNICAL_DEPTH
PS = ProfileDimension.PROBLEM_SOLVING
CO = ProfileDimension.COMMUNICATION


def test_empty_profile_returns_none():
    assert _calc.calculate(empty_profile()) is None


def test_single_dim_returns_it():
    p = CandidateProfile(dimension_scores={TD: mk_trace(ev=2)})
    assert _calc.calculate(p) == TD


def test_highest_evidence_count_wins():
    p = CandidateProfile(dimension_scores={
        TD: mk_trace(ev=5, avg=60.0),
        PS: mk_trace(ev=2, avg=70.0),
    })
    assert _calc.calculate(p) == TD


def test_tiebreak_lowest_avg_score():
    # Same evidence_count; lower avg → more problematic → dominant
    p = CandidateProfile(dimension_scores={
        TD: mk_trace(ev=3, avg=70.0),
        PS: mk_trace(ev=3, avg=40.0),
    })
    assert _calc.calculate(p) == PS


def test_reflects_full_session_not_cycle():
    # Accumulated evidence over many cycles
    p = CandidateProfile(dimension_scores={
        TD: mk_trace(ev=10, avg=55.0),
        CO: mk_trace(ev=3, avg=30.0),
    })
    assert _calc.calculate(p) == TD  # higher ev_count wins


def test_multiple_dims_all_equal():
    p = CandidateProfile(dimension_scores={
        TD: mk_trace(ev=3, avg=50.0),
        PS: mk_trace(ev=3, avg=50.0),
    })
    # Any deterministic answer is acceptable; just must not raise
    result = _calc.calculate(p)
    assert result in (TD, PS)
