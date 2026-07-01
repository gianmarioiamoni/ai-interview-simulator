# tests/services/interview_reasoner/pattern_detection/detectors/adaptability/test_analyzer.py
"""Tests for AdaptabilityAnalyzer."""

from __future__ import annotations

import uuid

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.adaptability.analyzer import (
    AdaptabilityAnalyzer,
    AdaptabilityStats,
    RECOVERY_WINDOW_QUESTIONS,
    MIN_BEHAVIORAL_SIGNALS,
)


def _sig(
    signal_type: EvidenceType,
    polarity: EvidencePolarity = EvidencePolarity.POSITIVE,
    dim: ProfileDimension = ProfileDimension.PROBLEM_SOLVING,
    area: str = "area_a",
    q_idx: int = 1,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=q_idx,
        question_area=area,
        dimension=dim,
        polarity=polarity,
        signal_type=signal_type,
        strength=0.7,
        source=EvidenceSource.PATTERN_DETECTOR,
        timestamp_question_index=q_idx,
    )


ANALYZER = AdaptabilityAnalyzer()


# ---- empty / guard -----------------------------------------------------------

def test_empty_signals_returns_zeroed_stats():
    stats = ANALYZER.analyze([])
    assert stats.total_behavioral_signals == 0
    assert stats.recovery_count == 0
    assert stats.rigidity_count == 0


def test_below_min_returns_zeroed():
    sigs = [_sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE)]
    assert len(sigs) < MIN_BEHAVIORAL_SIGNALS
    stats = ANALYZER.analyze(sigs)
    assert stats.recovery_count == 0


def test_non_behavioral_signals_ignored():
    sigs = [
        _sig(EvidenceType.SHALLOW_ANSWER, polarity=EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED),
        _sig(EvidenceType.REPEATED_STRENGTH),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.total_behavioral_signals == 0


# ---- recovery detection (ADR-065) -------------------------------------------

def test_recovery_within_window():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=1, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, q_idx=3, area="a"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.recovery_count == 1
    assert stats.rigidity_count == 0


def test_recovery_at_exact_window_boundary():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=1, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             q_idx=1 + RECOVERY_WINDOW_QUESTIONS, area="a"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.recovery_count == 1


def test_recovery_outside_window_is_rigidity():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=1, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             q_idx=1 + RECOVERY_WINDOW_QUESTIONS + 1, area="a"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.recovery_count == 0
    assert stats.rigidity_count == 1


def test_multiple_recoveries():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=1, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, q_idx=2, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=5, area="b"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, q_idx=7, area="b"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.recovery_count == 2
    assert stats.rigidity_count == 0


def test_instability_without_recovery_is_rigidity():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=1, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=2, area="b"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.rigidity_count == 2
    assert stats.recovery_count == 0


def test_growth_used_only_once():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=1, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=2, area="b"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, q_idx=3, area="a"),
    ]
    stats = ANALYZER.analyze(sigs)
    # Only one recovery possible with a single growth event
    assert stats.recovery_count == 1
    assert stats.rigidity_count == 1


# ---- flexibility count -------------------------------------------------------

def test_cross_area_consistent_positive_counts_flexibility():
    sigs = [
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="x", q_idx=1),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="y", q_idx=2),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="z", q_idx=3),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.flexibility_count == 3


def test_cross_area_consistent_negative_not_flexibility():
    sigs = [
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.NEGATIVE, area="x", q_idx=1),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.NEGATIVE, area="y", q_idx=2),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.NEGATIVE, area="z", q_idx=3),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.flexibility_count == 0


# ---- reframing events --------------------------------------------------------

def test_cross_area_contradictory_counts_reframing():
    sigs = [
        _sig(EvidenceType.CROSS_AREA_CONTRADICTORY, area="x", q_idx=1),
        _sig(EvidenceType.CROSS_AREA_CONTRADICTORY, area="y", q_idx=2),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.reframing_events == 2


# ---- adaptability_ratio ------------------------------------------------------

def test_adaptability_ratio_with_no_instability():
    stats = AdaptabilityStats()
    assert stats.adaptability_ratio == pytest.approx(0.0)  # 0 recovery / max(1, 0 instability) = 0.0


def test_adaptability_ratio_with_full_recovery():
    stats = AdaptabilityStats(recovery_count=3, total_instability_events=3)
    assert stats.adaptability_ratio == pytest.approx(1.0)


def test_adaptability_ratio_partial():
    stats = AdaptabilityStats(recovery_count=1, total_instability_events=4)
    assert stats.adaptability_ratio == pytest.approx(0.25)


# ---- trend -------------------------------------------------------------------

def test_trend_insufficient_when_no_data():
    stats = AdaptabilityStats()
    assert stats.trend == "INSUFFICIENT"


def test_trend_improving_recovery_greater_rigidity():
    stats = AdaptabilityStats(
        recovery_count=3, rigidity_count=1,
        flexibility_count=2,
        total_instability_events=4,
    )
    assert stats.trend == "IMPROVING"


def test_trend_declining_rigidity_greater_recovery():
    stats = AdaptabilityStats(
        recovery_count=1, rigidity_count=3,
        total_instability_events=4,
    )
    assert stats.trend == "DECLINING"


# ---- immutability ------------------------------------------------------------

def test_adaptability_stats_is_frozen():
    stats = AdaptabilityStats(recovery_count=2)
    with pytest.raises((AttributeError, TypeError)):
        stats.recovery_count = 99  # type: ignore[misc]
