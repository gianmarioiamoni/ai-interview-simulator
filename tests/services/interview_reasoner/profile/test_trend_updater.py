# tests/services/interview_reasoner/profile/test_trend_updater.py
"""Tests for TrendUpdater (M2-6C)."""

import pytest

from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from services.interview_reasoner.profile.trend_updater import TrendUpdater

from tests.services.interview_reasoner.profile.conftest import (
    empty_profile, mk_sig, mk_trace, profile_with_trace,
)

_upd = TrendUpdater()
TD = ProfileDimension.TECHNICAL_DEPTH


def test_empty_profile_unchanged():
    p = empty_profile()
    result = _upd.update(p, [], 1)
    assert result is p


def test_insufficient_data_below_3_evidence():
    p = profile_with_trace(TD, avg=60.0, last=80.0, ev=2)
    result = _upd.update(p, [], 1)
    assert result.dimension_scores[TD].trend == Trend.INSUFFICIENT_DATA


def test_improving_when_last_above_avg():
    # avg=50, last=62 → delta=12 > threshold(8)
    p = profile_with_trace(TD, avg=50.0, last=62.0, ev=5, trend=Trend.STABLE)
    result = _upd.update(p, [], 1)
    assert result.dimension_scores[TD].trend == Trend.IMPROVING


def test_declining_when_last_below_avg():
    # avg=60, last=48 → delta=-12 < -threshold(-8)
    p = profile_with_trace(TD, avg=60.0, last=48.0, ev=5, trend=Trend.STABLE)
    result = _upd.update(p, [], 1)
    assert result.dimension_scores[TD].trend == Trend.DECLINING


def test_stable_within_threshold():
    # avg=60, last=65 → delta=5 < threshold(8) → STABLE
    p = profile_with_trace(TD, avg=60.0, last=65.0, ev=5, trend=Trend.INSUFFICIENT_DATA)
    result = _upd.update(p, [], 1)
    assert result.dimension_scores[TD].trend == Trend.STABLE


def test_no_change_same_trend_returns_same_profile():
    p = profile_with_trace(TD, avg=60.0, last=65.0, ev=5, trend=Trend.STABLE)
    result = _upd.update(p, [], 1)
    # Stable→stable: no-op, same object
    assert result is p


def test_immutability():
    p = profile_with_trace(TD, avg=50.0, last=62.0, ev=5, trend=Trend.STABLE)
    _ = _upd.update(p, [], 1)
    assert p.dimension_scores[TD].trend == Trend.STABLE


def test_only_affected_dimension_trend_changes():
    from domain.contracts.reasoning.candidate_profile import CandidateProfile
    from domain.contracts.reasoning.profile_dimension import ProfileDimension as PD
    PS = PD.PROBLEM_SOLVING
    p = CandidateProfile(dimension_scores={
        TD: mk_trace(avg=50.0, last=62.0, ev=5, trend=Trend.STABLE),
        PS: mk_trace(avg=60.0, last=65.0, ev=5, trend=Trend.STABLE),
    })
    result = _upd.update(p, [], 1)
    assert result.dimension_scores[TD].trend == Trend.IMPROVING
    assert result.dimension_scores[PS].trend == Trend.STABLE
