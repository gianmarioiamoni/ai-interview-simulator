# tests/services/interview_reasoner/pattern_detection/detectors/reasoning_depth/test_signal_factory.py
"""Tests for ReasoningDepthSignalFactory."""

from __future__ import annotations

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.reasoning_depth.analyzer import (
    DimensionDepthStats,
)
from services.interview_reasoner.pattern_detection.detectors.reasoning_depth.scorer import (
    DepthVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.reasoning_depth.signal_factory import (
    ReasoningDepthSignalFactory,
)

FACTORY = ReasoningDepthSignalFactory()
DIM = ProfileDimension.TECHNICAL_DEPTH


def _stats(depth: int, shallow: int) -> DimensionDepthStats:
    return DimensionDepthStats(dimension=DIM, depth_count=depth, shallow_count=shallow)


# ---- make_depth_signal ---------------------------------------------------

def test_high_verdict_produces_depth_high_signal():
    sig = FACTORY.make_depth_signal(DepthVerdict.HIGH, _stats(5, 1), question_index=3, area="area")
    assert sig is not None
    assert sig.signal_type == EvidenceType.REASONING_DEPTH_HIGH
    assert sig.polarity == EvidencePolarity.POSITIVE
    assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_low_verdict_produces_depth_low_signal():
    sig = FACTORY.make_depth_signal(DepthVerdict.LOW, _stats(1, 5), question_index=3, area="area")
    assert sig is not None
    assert sig.signal_type == EvidenceType.REASONING_DEPTH_LOW
    assert sig.polarity == EvidencePolarity.NEGATIVE


def test_neutral_verdict_produces_none():
    sig = FACTORY.make_depth_signal(DepthVerdict.NEUTRAL, _stats(3, 3), question_index=3, area="area")
    assert sig is None


def test_depth_high_strength_from_ratio():
    stats = _stats(5, 0)  # ratio=1.0
    sig = FACTORY.make_depth_signal(DepthVerdict.HIGH, stats, question_index=1, area="a")
    assert sig.strength == 1.0


def test_depth_low_strength_from_ratio():
    stats = _stats(0, 5)  # ratio=0.0 → strength=1.0
    sig = FACTORY.make_depth_signal(DepthVerdict.LOW, stats, question_index=1, area="a")
    assert sig.strength == 1.0


# ---- make_trend_signal ---------------------------------------------------

def test_improving_trend_signal():
    sig = FACTORY.make_trend_signal(DepthVerdict.IMPROVING, DIM, question_index=5, area="x")
    assert sig is not None
    assert sig.signal_type == EvidenceType.REASONING_IMPROVING
    assert sig.polarity == EvidencePolarity.POSITIVE


def test_stagnating_trend_signal():
    sig = FACTORY.make_trend_signal(DepthVerdict.LOW, DIM, question_index=5, area="x")
    assert sig is not None
    assert sig.signal_type == EvidenceType.REASONING_STAGNATING
    assert sig.polarity == EvidencePolarity.NEGATIVE


def test_neutral_trend_produces_none():
    sig = FACTORY.make_trend_signal(DepthVerdict.NEUTRAL, DIM, question_index=5, area="x")
    assert sig is None


def test_trend_signal_dimension_preserved():
    dim = ProfileDimension.PROBLEM_SOLVING
    sig = FACTORY.make_trend_signal(DepthVerdict.IMPROVING, dim, question_index=2, area="a")
    assert sig.dimension == dim
