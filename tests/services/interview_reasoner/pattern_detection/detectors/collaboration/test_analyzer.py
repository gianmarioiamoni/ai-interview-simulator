# tests/services/interview_reasoner/pattern_detection/detectors/collaboration/test_analyzer.py
"""Tests for CollaborationAnalyzer."""

from __future__ import annotations

import uuid

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.collaboration.analyzer import (
    CollaborationAnalyzer,
    CollaborationStats,
    MIN_BEHAVIORAL_SIGNALS,
)


def _sig(
    signal_type: EvidenceType,
    polarity: EvidencePolarity = EvidencePolarity.POSITIVE,
    dim: ProfileDimension = ProfileDimension.COMMUNICATION,
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


ANALYZER = CollaborationAnalyzer()


# ---- empty / guard conditions -----------------------------------------------

def test_empty_signals_returns_zeroed_stats():
    stats = ANALYZER.analyze([])
    assert stats.total_behavioral_signals == 0
    assert stats.team_orientation_count == 0
    assert stats.collaboration_ratio == 0.0


def test_below_min_behavioral_signals_returns_zeroed():
    sigs = [_sig(EvidenceType.BEHAVIORAL_GROWTH)]
    assert len(sigs) < MIN_BEHAVIORAL_SIGNALS
    stats = ANALYZER.analyze(sigs)
    assert stats.team_orientation_count == 0


def test_non_behavioral_signals_ignored():
    sigs = [
        _sig(EvidenceType.SHALLOW_ANSWER, polarity=EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED),
        _sig(EvidenceType.REPEATED_STRENGTH),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.total_behavioral_signals == 0


# ---- team orientation --------------------------------------------------------

def test_behavioral_growth_on_communication_dim_counts_team():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="b"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="c"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.team_orientation_count == 3


def test_behavioral_growth_on_problem_solving_not_team_orientation():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="b"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="c"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.team_orientation_count == 0


def test_leadership_signal_enriches_team_orientation():
    sigs = [
        _sig(EvidenceType.LEADERSHIP_EMERGING, polarity=EvidencePolarity.POSITIVE, area="a"),
        _sig(EvidenceType.LEADERSHIP_STRONG, polarity=EvidencePolarity.POSITIVE, area="b"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="c"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.team_orientation_count >= 2


# ---- knowledge sharing -------------------------------------------------------

def test_cross_area_consistent_positive_counts_knowledge_sharing():
    sigs = [
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="x"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="y"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="z"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.knowledge_sharing_count == 3


def test_cross_area_consistent_negative_not_knowledge_sharing():
    sigs = [
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.NEGATIVE, area="x"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.NEGATIVE, area="y"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.NEGATIVE, area="z"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.knowledge_sharing_count == 0


# ---- cross-functional count --------------------------------------------------

def test_cross_area_consistent_distinct_areas_cross_functional():
    sigs = [
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="team_a"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="team_b"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="team_c"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.cross_functional_count == 3


def test_same_area_cross_area_consistent_single_cross_functional():
    sigs = [
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="same"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="same"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="same"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.cross_functional_count == 1


# ---- conflict signals --------------------------------------------------------

def test_instability_signals_counted_as_conflict():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="b"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="c"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.conflict_signals_count == 2


# ---- feedback acceptance / recovery -----------------------------------------

def test_recovery_after_instability_counts_feedback_acceptance():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="a", q_idx=1),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="b", q_idx=2),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="c", q_idx=3),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.feedback_acceptance_count >= 1


def test_no_instability_no_feedback_acceptance():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="b"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="c"),
    ]
    stats = ANALYZER.analyze(sigs)
    assert stats.feedback_acceptance_count == 0


# ---- conflict resolution ratio -----------------------------------------------

def test_conflict_resolution_ratio_one_when_no_conflict():
    stats = CollaborationStats(total_behavioral_signals=5)
    assert stats.conflict_resolution_ratio == 1.0


def test_conflict_resolution_ratio_computed():
    stats = CollaborationStats(
        conflict_signals_count=4,
        positive_conflict_count=3,
        total_behavioral_signals=10,
    )
    assert stats.conflict_resolution_ratio == pytest.approx(0.75)


# ---- collaboration_ratio -----------------------------------------------------

def test_collaboration_ratio_zero_when_no_signals():
    stats = CollaborationStats()
    assert stats.collaboration_ratio == 0.0


def test_collaboration_ratio_computed():
    stats = CollaborationStats(
        team_orientation_count=2,
        knowledge_sharing_count=1,
        feedback_acceptance_count=1,
        total_behavioral_signals=8,
    )
    assert stats.collaboration_ratio == pytest.approx(4 / 8)


# ---- trend -------------------------------------------------------------------

def test_trend_insufficient_when_below_min():
    stats = CollaborationStats(total_behavioral_signals=1)
    assert stats.trend == "INSUFFICIENT"


def test_trend_rising_when_high_collab():
    stats = CollaborationStats(
        team_orientation_count=3,
        knowledge_sharing_count=2,
        total_behavioral_signals=8,
    )
    assert stats.trend == "RISING"


def test_trend_declining_when_no_collab():
    stats = CollaborationStats(
        team_orientation_count=0,
        knowledge_sharing_count=0,
        total_behavioral_signals=10,
    )
    assert stats.trend == "DECLINING"


# ---- immutability ------------------------------------------------------------

def test_collaboration_stats_is_frozen():
    stats = CollaborationStats(team_orientation_count=2, total_behavioral_signals=5)
    with pytest.raises((AttributeError, TypeError)):
        stats.team_orientation_count = 99  # type: ignore[misc]
