# tests/services/interview_reasoner/pattern_detection/detectors/communication/test_signal_factory.py
"""Tests for CommunicationSignalFactory."""

from __future__ import annotations

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.communication.analyzer import (
    CommunicationStats,
)
from services.interview_reasoner.pattern_detection.detectors.communication.scorer import (
    CommunicationVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.communication.signal_factory import (
    CommunicationSignalFactory,
)

FACTORY = CommunicationSignalFactory()


def _stats(positive: int, negative: int, inconsistent: int = 0) -> CommunicationStats:
    return CommunicationStats(
        positive_count=positive,
        negative_count=negative,
        inconsistent_count=inconsistent,
    )


def test_clear_verdict_produces_positive_signal():
    sig = FACTORY.make_signal(CommunicationVerdict.CLEAR, _stats(4, 1), 3, "area")
    assert sig is not None
    assert sig.signal_type == EvidenceType.COMMUNICATION_CLEAR
    assert sig.polarity == EvidencePolarity.POSITIVE
    assert sig.dimension == ProfileDimension.COMMUNICATION
    assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_weak_verdict_produces_negative_signal():
    sig = FACTORY.make_signal(CommunicationVerdict.WEAK, _stats(1, 4), 2, "area")
    assert sig is not None
    assert sig.signal_type == EvidenceType.COMMUNICATION_WEAK
    assert sig.polarity == EvidencePolarity.NEGATIVE
    assert sig.dimension == ProfileDimension.COMMUNICATION


def test_inconsistent_verdict_produces_negative_signal():
    sig = FACTORY.make_signal(CommunicationVerdict.INCONSISTENT, _stats(2, 1, inconsistent=2), 1, "area")
    assert sig is not None
    assert sig.signal_type == EvidenceType.COMMUNICATION_INCONSISTENT
    assert sig.polarity == EvidencePolarity.NEGATIVE
    assert sig.dimension == ProfileDimension.COMMUNICATION


def test_neutral_verdict_returns_none():
    sig = FACTORY.make_signal(CommunicationVerdict.NEUTRAL, _stats(2, 2), 1, "area")
    assert sig is None


def test_clear_signal_strength_from_ratio():
    stats = _stats(4, 1)  # ratio = 0.8
    sig = FACTORY.make_signal(CommunicationVerdict.CLEAR, stats, 1, "area")
    assert sig is not None
    assert sig.strength == pytest.approx(0.8)


def test_weak_signal_strength_inverted():
    stats = _stats(1, 4)  # ratio = 0.2, strength = 1 - 0.2 = 0.8
    sig = FACTORY.make_signal(CommunicationVerdict.WEAK, stats, 1, "area")
    assert sig is not None
    assert sig.strength == pytest.approx(0.8)


def test_inconsistent_signal_strength_based_on_ratio():
    stats = _stats(0, 0, inconsistent=2)  # 2/2 = 1.0
    sig = FACTORY.make_signal(CommunicationVerdict.INCONSISTENT, stats, 1, "area")
    assert sig is not None
    assert sig.strength <= 1.0
    assert sig.strength >= 0.0


def test_signal_question_index_set():
    sig = FACTORY.make_signal(CommunicationVerdict.CLEAR, _stats(3, 0), 7, "databases")
    assert sig is not None
    assert sig.question_index == 7
    assert sig.timestamp_question_index == 7


def test_signal_area_set():
    sig = FACTORY.make_signal(CommunicationVerdict.CLEAR, _stats(3, 0), 1, "concurrency")
    assert sig is not None
    assert sig.question_area == "concurrency"


def test_signal_id_is_unique():
    stats = _stats(3, 0)
    sig1 = FACTORY.make_signal(CommunicationVerdict.CLEAR, stats, 1, "area")
    sig2 = FACTORY.make_signal(CommunicationVerdict.CLEAR, stats, 1, "area")
    assert sig1 is not None and sig2 is not None
    assert sig1.id != sig2.id
