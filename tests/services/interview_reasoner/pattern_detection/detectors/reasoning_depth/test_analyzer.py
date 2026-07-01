# tests/services/interview_reasoner/pattern_detection/detectors/reasoning_depth/test_analyzer.py
"""Tests for ReasoningDepthAnalyzer."""

from __future__ import annotations

import uuid
import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.reasoning_depth.analyzer import (
    ReasoningDepthAnalyzer,
    DEEP_TYPES,
    SHALLOW_TYPES,
    DimensionDepthStats,
)


def _sig(
    signal_type: EvidenceType,
    polarity: EvidencePolarity,
    dim: ProfileDimension = ProfileDimension.TECHNICAL_DEPTH,
    q_idx: int = 0,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=q_idx,
        question_area="area",
        dimension=dim,
        polarity=polarity,
        signal_type=signal_type,
        strength=0.7,
        source=EvidenceSource.EVALUATION,
        timestamp_question_index=q_idx,
    )


ANALYZER = ReasoningDepthAnalyzer()


def test_no_signals_returns_empty():
    result = ANALYZER.analyze([])
    assert result == {}


def test_deep_signal_positive_counted():
    sigs = [_sig(EvidenceType.DEMONSTRATED_DEPTH, EvidencePolarity.POSITIVE)]
    result = ANALYZER.analyze(sigs)
    stats = result[ProfileDimension.TECHNICAL_DEPTH]
    assert stats.depth_count == 1
    assert stats.shallow_count == 0


def test_shallow_signal_negative_counted():
    sigs = [_sig(EvidenceType.SHALLOW_ANSWER, EvidencePolarity.NEGATIVE)]
    result = ANALYZER.analyze(sigs)
    stats = result[ProfileDimension.TECHNICAL_DEPTH]
    assert stats.shallow_count == 1
    assert stats.depth_count == 0


def test_deep_signal_negative_polarity_not_counted_as_depth():
    sigs = [_sig(EvidenceType.DEMONSTRATED_DEPTH, EvidencePolarity.NEGATIVE)]
    result = ANALYZER.analyze(sigs)
    stats = result[ProfileDimension.TECHNICAL_DEPTH]
    assert stats.depth_count == 0
    assert stats.shallow_count == 0


def test_shallow_signal_positive_polarity_not_counted_as_shallow():
    sigs = [_sig(EvidenceType.SHALLOW_ANSWER, EvidencePolarity.POSITIVE)]
    result = ANALYZER.analyze(sigs)
    stats = result[ProfileDimension.TECHNICAL_DEPTH]
    assert stats.shallow_count == 0


def test_depth_ratio_neutral_when_no_signals():
    stats = DimensionDepthStats(dimension=ProfileDimension.TECHNICAL_DEPTH)
    assert stats.depth_ratio == 0.5


def test_depth_ratio_all_deep():
    stats = DimensionDepthStats(
        dimension=ProfileDimension.TECHNICAL_DEPTH, depth_count=3, shallow_count=0
    )
    assert stats.depth_ratio == 1.0


def test_depth_ratio_all_shallow():
    stats = DimensionDepthStats(
        dimension=ProfileDimension.TECHNICAL_DEPTH, depth_count=0, shallow_count=3
    )
    assert stats.depth_ratio == 0.0


def test_depth_ratio_mixed():
    stats = DimensionDepthStats(
        dimension=ProfileDimension.TECHNICAL_DEPTH, depth_count=2, shallow_count=2
    )
    assert stats.depth_ratio == 0.5


def test_multi_dimension_split():
    sigs = [
        _sig(EvidenceType.DEMONSTRATED_DEPTH, EvidencePolarity.POSITIVE, ProfileDimension.TECHNICAL_DEPTH),
        _sig(EvidenceType.SHALLOW_ANSWER, EvidencePolarity.NEGATIVE, ProfileDimension.PROBLEM_SOLVING),
    ]
    result = ANALYZER.analyze(sigs)
    assert result[ProfileDimension.TECHNICAL_DEPTH].depth_count == 1
    assert result[ProfileDimension.PROBLEM_SOLVING].shallow_count == 1


def test_irrelevant_signal_types_not_counted():
    sigs = [
        _sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.REPEATED_WEAKNESS, EvidencePolarity.NEGATIVE),
    ]
    result = ANALYZER.analyze(sigs)
    stats = result[ProfileDimension.TECHNICAL_DEPTH]
    assert stats.depth_count == 0
    assert stats.shallow_count == 0
