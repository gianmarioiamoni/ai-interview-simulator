# tests/services/interview_reasoner/pattern_detection/detectors/leadership/test_analyzer.py
"""Tests for LeadershipAnalyzer."""

from __future__ import annotations

import uuid

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.leadership.analyzer import (
    LeadershipAnalyzer,
    LeadershipStats,
    MIN_BEHAVIORAL_SIGNALS,
    MIN_AREAS_FOR_STRATEGIC,
)


def _sig(
    signal_type: EvidenceType,
    polarity: EvidencePolarity = EvidencePolarity.POSITIVE,
    dim: ProfileDimension = ProfileDimension.PROBLEM_SOLVING,
    area: str = "area_a",
    q_idx: int = 1,
    source: EvidenceSource = EvidenceSource.PATTERN_DETECTOR,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=q_idx,
        question_area=area,
        dimension=dim,
        polarity=polarity,
        signal_type=signal_type,
        strength=0.7,
        source=source,
        timestamp_question_index=q_idx,
    )


ANALYZER = LeadershipAnalyzer()

# ---- empty / guard conditions -----------------------------------------------

def test_empty_signals_returns_zeroed_stats():
    stats = ANALYZER.analyze([])
    assert stats.total_behavioral_signals == 0
    assert stats.ownership_signal_count == 0
    assert stats.initiative_signal_count == 0
    assert stats.accountability_signal_count == 0
    assert stats.leadership_ratio == 0.0


def test_below_min_signals_returns_zeroed_stats():
    sigs = [_sig(EvidenceType.BEHAVIORAL_GROWTH)]
    assert len(sigs) < MIN_BEHAVIORAL_SIGNALS
    stats = ANALYZER.analyze(sigs)
    assert stats.ownership_signal_count == 0
    assert stats.leadership_ratio == 0.0


def test_non_behavioral_signals_ignored():
    sigs = [
        _sig(EvidenceType.SHALLOW_ANSWER, polarity=EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, polarity=EvidencePolarity.POSITIVE),
        _sig(EvidenceType.REPEATED_STRENGTH, polarity=EvidencePolarity.POSITIVE),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.total_behavioral_signals == 0


# ---- ownership ---------------------------------------------------------------

def test_behavioral_growth_on_problem_solving_counts_as_ownership():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="b"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="c"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.ownership_signal_count == 3


def test_behavioral_growth_on_other_dim_not_ownership():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="b"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="c"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.ownership_signal_count == 0


# ---- initiative ---------------------------------------------------------------

def test_growth_in_two_areas_counts_initiative():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, area="area_x"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, area="area_y"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, area="area_z"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.initiative_signal_count >= 1


def test_growth_in_single_area_no_initiative():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, area="same"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, area="same"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, area="same"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.initiative_signal_count == 0


# ---- accountability (recovery) -----------------------------------------------

def test_growth_after_instability_counts_accountability():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="a", q_idx=1),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, area="a", q_idx=2),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, area="b", q_idx=3),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.accountability_signal_count >= 1


def test_no_instability_no_accountability():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, area="b"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, area="c"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.accountability_signal_count == 0


# ---- mentoring ---------------------------------------------------------------

def test_cross_area_consistent_positive_counts_mentoring():
    sigs = [
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="a"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="b"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="c"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.mentoring_signal_count >= 1


def test_cross_area_consistent_negative_not_mentoring():
    sigs = [
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.NEGATIVE, area="a"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.NEGATIVE, area="b"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.NEGATIVE, area="c"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.mentoring_signal_count == 0


# ---- strategic ---------------------------------------------------------------

def test_cross_area_consistent_in_three_areas_strategic():
    sigs = [
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="x"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="y"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="z"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.strategic_signal_count == 1


def test_cross_area_consistent_in_two_areas_not_strategic():
    sigs = [
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="x"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="x"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="y"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.strategic_signal_count == 0


# ---- trend -------------------------------------------------------------------

def test_trend_insufficient_when_below_min():
    stats = LeadershipStats(total_behavioral_signals=1)
    assert stats.trend == "INSUFFICIENT"


def test_trend_rising_when_high_ownership_initiative():
    stats = LeadershipStats(
        ownership_signal_count=3,
        initiative_signal_count=2,
        total_behavioral_signals=8,
    )
    assert stats.trend == "RISING"


def test_trend_declining_when_no_ownership_initiative():
    stats = LeadershipStats(
        ownership_signal_count=0,
        initiative_signal_count=0,
        accountability_signal_count=1,
        total_behavioral_signals=10,
    )
    assert stats.trend == "DECLINING"


# ---- immutability ------------------------------------------------------------

def test_leadership_stats_is_frozen():
    stats = LeadershipStats(ownership_signal_count=2, total_behavioral_signals=5)
    with pytest.raises((AttributeError, TypeError)):
        stats.ownership_signal_count = 99  # type: ignore[misc]


# ---- active dimension count --------------------------------------------------

def test_active_dimension_count_correct():
    stats = LeadershipStats(
        ownership_signal_count=1,
        initiative_signal_count=0,
        accountability_signal_count=1,
        mentoring_signal_count=0,
        strategic_signal_count=1,
        total_behavioral_signals=5,
    )
    assert stats.active_dimension_count == 3
