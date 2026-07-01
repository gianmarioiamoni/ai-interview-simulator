# tests/services/interview_reasoner/pattern_detection/detectors/leadership/test_signal_factory.py
"""Tests for LeadershipSignalFactory."""

from __future__ import annotations

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.leadership.analyzer import (
    LeadershipStats,
)
from services.interview_reasoner.pattern_detection.detectors.leadership.scorer import (
    LeadershipVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.leadership.signal_factory import (
    LeadershipSignalFactory,
)

FACTORY = LeadershipSignalFactory()


def _stats(
    ownership: int = 0,
    initiative: int = 0,
    accountability: int = 0,
    total: int = 5,
) -> LeadershipStats:
    return LeadershipStats(
        ownership_signal_count=ownership,
        initiative_signal_count=initiative,
        accountability_signal_count=accountability,
        total_behavioral_signals=total,
    )


# ---- NEUTRAL → None ----------------------------------------------------------

def test_neutral_returns_none():
    result = FACTORY.create(LeadershipVerdict.NEUTRAL, _stats(), 1, "area")
    assert result is None


# ---- STRONG_LEADER -----------------------------------------------------------

def test_strong_leader_signal_type():
    stats = _stats(ownership=3, initiative=2, accountability=1, total=8)
    sig = FACTORY.create(LeadershipVerdict.STRONG_LEADER, stats, 2, "leadership")
    assert sig is not None
    assert sig.signal_type == EvidenceType.LEADERSHIP_STRONG


def test_strong_leader_positive_polarity():
    stats = _stats(ownership=3, initiative=2, accountability=1, total=8)
    sig = FACTORY.create(LeadershipVerdict.STRONG_LEADER, stats, 2, "leadership")
    assert sig.polarity == EvidencePolarity.POSITIVE


def test_strong_leader_dimension_problem_solving():
    stats = _stats(ownership=3, initiative=2, accountability=1, total=8)
    sig = FACTORY.create(LeadershipVerdict.STRONG_LEADER, stats, 2, "leadership")
    assert sig.dimension == ProfileDimension.PROBLEM_SOLVING


def test_strong_leader_strength_clamped_to_one():
    # ratio = 6/8 = 0.75, strength = min(1.0, 0.75 * 1.5) = 1.0
    stats = _stats(ownership=4, initiative=2, total=8)
    sig = FACTORY.create(LeadershipVerdict.STRONG_LEADER, stats, 2, "area")
    assert sig.strength <= 1.0


def test_strong_leader_strength_formula():
    # ratio = 4/8 = 0.5, strength = min(1.0, 0.5 * 1.5) = 0.75
    stats = LeadershipStats(ownership_signal_count=2, initiative_signal_count=2, total_behavioral_signals=8)
    sig = FACTORY.create(LeadershipVerdict.STRONG_LEADER, stats, 1, "area")
    assert sig.strength == pytest.approx(0.75, abs=0.01)


# ---- EMERGING_LEADER ---------------------------------------------------------

def test_emerging_leader_signal_type():
    stats = _stats(ownership=2, total=5)
    sig = FACTORY.create(LeadershipVerdict.EMERGING_LEADER, stats, 3, "area")
    assert sig.signal_type == EvidenceType.LEADERSHIP_EMERGING


def test_emerging_leader_positive_polarity():
    stats = _stats(ownership=2, total=5)
    sig = FACTORY.create(LeadershipVerdict.EMERGING_LEADER, stats, 3, "area")
    assert sig.polarity == EvidencePolarity.POSITIVE


def test_emerging_leader_strength_equals_ratio():
    stats = _stats(ownership=2, total=5)
    sig = FACTORY.create(LeadershipVerdict.EMERGING_LEADER, stats, 3, "area")
    assert sig.strength == pytest.approx(stats.leadership_ratio, abs=0.01)


# ---- LEADERSHIP_ABSENT -------------------------------------------------------

def test_leadership_absent_signal_type():
    stats = LeadershipStats(total_behavioral_signals=5)
    sig = FACTORY.create(LeadershipVerdict.LEADERSHIP_ABSENT, stats, 4, "area")
    assert sig.signal_type == EvidenceType.LEADERSHIP_ABSENT


def test_leadership_absent_negative_polarity():
    stats = LeadershipStats(total_behavioral_signals=5)
    sig = FACTORY.create(LeadershipVerdict.LEADERSHIP_ABSENT, stats, 4, "area")
    assert sig.polarity == EvidencePolarity.NEGATIVE


def test_leadership_absent_fixed_strength():
    stats = LeadershipStats(total_behavioral_signals=5)
    sig = FACTORY.create(LeadershipVerdict.LEADERSHIP_ABSENT, stats, 4, "area")
    assert sig.strength == pytest.approx(0.4)


# ---- source and idempotency keys ---------------------------------------------

def test_signal_source_is_pattern_detector():
    stats = _stats(ownership=3, initiative=2, accountability=1, total=8)
    sig = FACTORY.create(LeadershipVerdict.STRONG_LEADER, stats, 2, "area")
    assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_signal_ids_are_unique():
    stats = _stats(ownership=3, initiative=2, accountability=1, total=8)
    sig1 = FACTORY.create(LeadershipVerdict.STRONG_LEADER, stats, 2, "area")
    sig2 = FACTORY.create(LeadershipVerdict.STRONG_LEADER, stats, 2, "area")
    assert sig1.id != sig2.id


def test_signal_question_index_correct():
    stats = _stats(ownership=2, total=5)
    sig = FACTORY.create(LeadershipVerdict.EMERGING_LEADER, stats, 7, "area")
    assert sig.question_index == 7
    assert sig.timestamp_question_index == 7


def test_signal_area_correct():
    stats = _stats(ownership=2, total=5)
    sig = FACTORY.create(LeadershipVerdict.EMERGING_LEADER, stats, 3, "leadership_area")
    assert sig.question_area == "leadership_area"
