# tests/services/interview_reasoner/pattern_detection/detectors/behavioral_pattern/test_signal_factory.py
"""Tests for BehaviorSignalFactory."""

from __future__ import annotations

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern.analyzer import (
    BehavioralStats,
    MIN_ENTRIES,
)
from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern.scorer import (
    BehaviorVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern.signal_factory import (
    BehaviorSignalFactory,
)

FACTORY = BehaviorSignalFactory()


def _stats(**kwargs) -> BehavioralStats:
    defaults = dict(
        entry_count=MIN_ENTRIES,
        confidence_trend=0.1,
        positive_ratio=0.7,
        variance_score=0.2,
        has_growth=False,
        has_instability=False,
        has_plateau=False,
    )
    defaults.update(kwargs)
    return BehavioralStats(**defaults)


def test_growth_produces_positive_signal():
    sig = FACTORY.make_signal(BehaviorVerdict.GROWTH, _stats(), 3, "area")
    assert sig is not None
    assert sig.signal_type == EvidenceType.BEHAVIORAL_GROWTH
    assert sig.polarity == EvidencePolarity.POSITIVE
    assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_instability_produces_negative_signal():
    sig = FACTORY.make_signal(BehaviorVerdict.INSTABILITY, _stats(variance_score=0.8), 3, "area")
    assert sig is not None
    assert sig.signal_type == EvidenceType.BEHAVIORAL_INSTABILITY
    assert sig.polarity == EvidencePolarity.NEGATIVE
    assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_plateau_produces_negative_signal():
    sig = FACTORY.make_signal(BehaviorVerdict.PLATEAU, _stats(), 3, "area")
    assert sig is not None
    assert sig.signal_type == EvidenceType.BEHAVIORAL_PLATEAU
    assert sig.polarity == EvidencePolarity.NEGATIVE


def test_neutral_returns_none():
    sig = FACTORY.make_signal(BehaviorVerdict.NEUTRAL, _stats(), 3, "area")
    assert sig is None


def test_dimension_is_problem_solving():
    sig = FACTORY.make_signal(BehaviorVerdict.GROWTH, _stats(), 1, "area")
    assert sig is not None
    assert sig.dimension == ProfileDimension.PROBLEM_SOLVING


def test_growth_strength_capped_at_one():
    sig = FACTORY.make_signal(BehaviorVerdict.GROWTH, _stats(positive_ratio=1.0), 1, "area")
    assert sig is not None
    assert sig.strength <= 1.0


def test_instability_strength_from_variance():
    sig = FACTORY.make_signal(BehaviorVerdict.INSTABILITY, _stats(variance_score=0.75), 1, "area")
    assert sig is not None
    assert sig.strength == pytest.approx(0.75)


def test_question_index_set():
    sig = FACTORY.make_signal(BehaviorVerdict.GROWTH, _stats(), 7, "area")
    assert sig is not None
    assert sig.question_index == 7
    assert sig.timestamp_question_index == 7


def test_area_set():
    sig = FACTORY.make_signal(BehaviorVerdict.GROWTH, _stats(), 1, "databases")
    assert sig is not None
    assert sig.question_area == "databases"


def test_unique_ids():
    s1 = FACTORY.make_signal(BehaviorVerdict.GROWTH, _stats(), 1, "area")
    s2 = FACTORY.make_signal(BehaviorVerdict.GROWTH, _stats(), 1, "area")
    assert s1 is not None and s2 is not None
    assert s1.id != s2.id
