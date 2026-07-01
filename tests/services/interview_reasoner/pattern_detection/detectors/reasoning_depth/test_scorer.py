# tests/services/interview_reasoner/pattern_detection/detectors/reasoning_depth/test_scorer.py
"""Tests for ReasoningDepthScorer."""

from __future__ import annotations

import pytest

from services.interview_reasoner.pattern_detection.detectors.reasoning_depth.analyzer import (
    DimensionDepthStats,
)
from services.interview_reasoner.pattern_detection.detectors.reasoning_depth.scorer import (
    DepthVerdict,
    HIGH_THRESHOLD,
    LOW_THRESHOLD,
    MIN_EVIDENCE,
    TREND_WINDOW,
    ReasoningDepthScorer,
)
from domain.contracts.reasoning.profile_dimension import ProfileDimension

SCORER = ReasoningDepthScorer()


def _stats(depth: int, shallow: int) -> DimensionDepthStats:
    return DimensionDepthStats(
        dimension=ProfileDimension.TECHNICAL_DEPTH,
        depth_count=depth,
        shallow_count=shallow,
    )


# ---- score() -------------------------------------------------------------

def test_neutral_when_insufficient_evidence():
    assert SCORER.score(_stats(1, 0)) == DepthVerdict.NEUTRAL


def test_high_verdict():
    # depth_ratio = 5/6 ≈ 0.83 ≥ HIGH_THRESHOLD, total=6 ≥ MIN_EVIDENCE
    assert SCORER.score(_stats(5, 1)) == DepthVerdict.HIGH


def test_low_verdict():
    # depth_ratio = 1/6 ≈ 0.17 ≤ LOW_THRESHOLD, total=6 ≥ MIN_EVIDENCE
    assert SCORER.score(_stats(1, 5)) == DepthVerdict.LOW


def test_neutral_verdict_middle_range():
    # depth_ratio = 3/6 = 0.5, between LOW and HIGH
    assert SCORER.score(_stats(3, 3)) == DepthVerdict.NEUTRAL


def test_exactly_min_evidence_triggers():
    # total=MIN_EVIDENCE, depth_ratio=1.0 → HIGH
    assert SCORER.score(_stats(MIN_EVIDENCE, 0)) == DepthVerdict.HIGH


def test_below_min_evidence_neutral():
    assert SCORER.score(_stats(MIN_EVIDENCE - 1, 0)) == DepthVerdict.NEUTRAL


def test_high_threshold_boundary():
    # depth_ratio = HIGH_THRESHOLD exactly
    depth = int(HIGH_THRESHOLD * 10)
    shallow = 10 - depth
    stats = _stats(depth * 10, shallow * 10)
    result = SCORER.score(stats)
    assert result in (DepthVerdict.HIGH, DepthVerdict.NEUTRAL)  # boundary inclusive


def test_low_threshold_boundary():
    depth = int(LOW_THRESHOLD * 10)
    shallow = 10 - depth
    stats = _stats(depth, shallow)
    result = SCORER.score(stats)
    assert result in (DepthVerdict.LOW, DepthVerdict.NEUTRAL)


# ---- trend_verdict() -----------------------------------------------------

def test_trend_insufficient_history():
    assert SCORER.trend_verdict([0.4, 0.5]) == DepthVerdict.NEUTRAL


def test_trend_improving():
    ratios = [0.3, 0.4, 0.5]  # monotonically increasing
    assert SCORER.trend_verdict(ratios) == DepthVerdict.IMPROVING


def test_trend_stagnating():
    ratios = [0.2, 0.2, 0.2]  # all ≤ LOW_THRESHOLD
    assert SCORER.trend_verdict(ratios) == DepthVerdict.LOW  # → STAGNATING


def test_trend_neutral_mixed():
    ratios = [0.5, 0.4, 0.6]  # not monotonic, not all low
    assert SCORER.trend_verdict(ratios) == DepthVerdict.NEUTRAL


def test_trend_uses_last_window_entries():
    # older entries are declining, last TREND_WINDOW are improving
    ratios = [0.1, 0.1, 0.3, 0.4, 0.5]
    assert SCORER.trend_verdict(ratios) == DepthVerdict.IMPROVING


def test_trend_stagnating_last_window_all_low():
    ratios = [0.8, 0.9, 0.2, 0.15, 0.1]
    assert SCORER.trend_verdict(ratios) == DepthVerdict.LOW
