# tests/services/interview_reasoner/pattern_detection/detectors/adaptability/test_signal_factory.py
"""Tests for AdaptabilitySignalFactory."""

from __future__ import annotations

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.adaptability.analyzer import (
    AdaptabilityStats,
)
from services.interview_reasoner.pattern_detection.detectors.adaptability.scorer import (
    AdaptabilityVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.adaptability.signal_factory import (
    AdaptabilitySignalFactory,
)

FACTORY = AdaptabilitySignalFactory()


def _stats(
    recovery: int = 0,
    rigidity: int = 0,
    flexibility: int = 0,
    context_switch: int = 1,
    total_instability: int = 0,
    total_behavioral: int = 5,
) -> AdaptabilityStats:
    return AdaptabilityStats(
        recovery_count=recovery,
        rigidity_count=rigidity,
        flexibility_count=flexibility,
        context_switch_count=context_switch,
        total_instability_events=total_instability,
        total_behavioral_signals=total_behavioral,
    )


# ---- NEUTRAL → None ----------------------------------------------------------

def test_neutral_returns_none():
    result = FACTORY.create(AdaptabilityVerdict.NEUTRAL, _stats(), 1, "area")
    assert result is None


# ---- HIGHLY_ADAPTABLE --------------------------------------------------------

def test_highly_adaptable_signal_type():
    stats = _stats(recovery=7, total_instability=10)
    sig = FACTORY.create(AdaptabilityVerdict.HIGHLY_ADAPTABLE, stats, 2, "area")
    assert sig is not None
    assert sig.signal_type == EvidenceType.ADAPTABILITY_HIGH


def test_highly_adaptable_positive_polarity():
    stats = _stats(recovery=7, total_instability=10)
    sig = FACTORY.create(AdaptabilityVerdict.HIGHLY_ADAPTABLE, stats, 2, "area")
    assert sig.polarity == EvidencePolarity.POSITIVE


def test_highly_adaptable_dimension_problem_solving():
    stats = _stats(recovery=7, total_instability=10)
    sig = FACTORY.create(AdaptabilityVerdict.HIGHLY_ADAPTABLE, stats, 2, "area")
    assert sig.dimension == ProfileDimension.PROBLEM_SOLVING


def test_highly_adaptable_strength_formula():
    # ratio = 7/10 = 0.7, strength = min(1.0, 0.7 * 1.3) = 0.91
    stats = _stats(recovery=7, total_instability=10)
    sig = FACTORY.create(AdaptabilityVerdict.HIGHLY_ADAPTABLE, stats, 2, "area")
    assert sig.strength == pytest.approx(0.91, abs=0.01)


def test_highly_adaptable_strength_clamped():
    stats = _stats(recovery=10, total_instability=10)
    sig = FACTORY.create(AdaptabilityVerdict.HIGHLY_ADAPTABLE, stats, 2, "area")
    assert sig.strength <= 1.0


# ---- ADAPTABLE ---------------------------------------------------------------

def test_adaptable_signal_type():
    stats = _stats(recovery=2, total_instability=5, flexibility=2, context_switch=2)
    sig = FACTORY.create(AdaptabilityVerdict.ADAPTABLE, stats, 3, "area")
    assert sig.signal_type == EvidenceType.ADAPTABILITY_MODERATE


def test_adaptable_positive_polarity():
    stats = _stats(recovery=2, total_instability=5, flexibility=2, context_switch=2)
    sig = FACTORY.create(AdaptabilityVerdict.ADAPTABLE, stats, 3, "area")
    assert sig.polarity == EvidencePolarity.POSITIVE


def test_adaptable_strength_max_of_ratios():
    stats = _stats(recovery=2, total_instability=5, flexibility=2, context_switch=2)
    sig = FACTORY.create(AdaptabilityVerdict.ADAPTABLE, stats, 3, "area")
    expected = max(stats.adaptability_ratio, stats.flexibility_ratio)
    assert sig.strength == pytest.approx(min(1.0, expected), abs=0.01)


# ---- LOW_ADAPTABILITY --------------------------------------------------------

def test_low_adaptability_signal_type():
    stats = _stats(recovery=0, rigidity=3, total_instability=3)
    sig = FACTORY.create(AdaptabilityVerdict.LOW_ADAPTABILITY, stats, 4, "area")
    assert sig.signal_type == EvidenceType.ADAPTABILITY_LOW


def test_low_adaptability_negative_polarity():
    stats = _stats(recovery=0, rigidity=3, total_instability=3)
    sig = FACTORY.create(AdaptabilityVerdict.LOW_ADAPTABILITY, stats, 4, "area")
    assert sig.polarity == EvidencePolarity.NEGATIVE


def test_low_adaptability_strength_formula():
    # rigidity=3, strength = min(1.0, 3/5.0) = 0.6
    stats = _stats(recovery=0, rigidity=3, total_instability=3)
    sig = FACTORY.create(AdaptabilityVerdict.LOW_ADAPTABILITY, stats, 4, "area")
    assert sig.strength == pytest.approx(0.6, abs=0.01)


# ---- source and metadata -----------------------------------------------------

def test_signal_source_is_pattern_detector():
    stats = _stats(recovery=7, total_instability=10)
    sig = FACTORY.create(AdaptabilityVerdict.HIGHLY_ADAPTABLE, stats, 2, "area")
    assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_signal_ids_are_unique():
    stats = _stats(recovery=7, total_instability=10)
    sig1 = FACTORY.create(AdaptabilityVerdict.HIGHLY_ADAPTABLE, stats, 2, "area")
    sig2 = FACTORY.create(AdaptabilityVerdict.HIGHLY_ADAPTABLE, stats, 2, "area")
    assert sig1.id != sig2.id


def test_signal_question_index_correct():
    stats = _stats(recovery=2, total_instability=5)
    sig = FACTORY.create(AdaptabilityVerdict.ADAPTABLE, stats, 9, "area")
    assert sig.question_index == 9
    assert sig.timestamp_question_index == 9


def test_signal_area_correct():
    stats = _stats(recovery=2, total_instability=5)
    sig = FACTORY.create(AdaptabilityVerdict.ADAPTABLE, stats, 3, "adapt_area")
    assert sig.question_area == "adapt_area"


def test_never_generates_collaboration_signals():
    for verdict in [AdaptabilityVerdict.HIGHLY_ADAPTABLE, AdaptabilityVerdict.ADAPTABLE, AdaptabilityVerdict.LOW_ADAPTABILITY]:
        stats = _stats(recovery=5, rigidity=2, total_instability=7, flexibility=3)
        sig = FACTORY.create(verdict, stats, 1, "area")
        if sig is not None:
            assert sig.signal_type not in (
                EvidenceType.COLLABORATION_STRONG,
                EvidenceType.COLLABORATION_EFFECTIVE,
                EvidenceType.COLLABORATION_DEFICIT,
                EvidenceType.LEADERSHIP_STRONG,
                EvidenceType.LEADERSHIP_EMERGING,
                EvidenceType.LEADERSHIP_ABSENT,
            )
