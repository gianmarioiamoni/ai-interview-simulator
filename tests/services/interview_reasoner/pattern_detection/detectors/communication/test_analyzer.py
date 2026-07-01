# tests/services/interview_reasoner/pattern_detection/detectors/communication/test_analyzer.py
"""Tests for CommunicationObservationExtractor."""

from __future__ import annotations

import uuid

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.communication.analyzer import (
    CommunicationObservationExtractor,
    CommunicationStats,
)

EXTRACTOR = CommunicationObservationExtractor()
_DIM = ProfileDimension.COMMUNICATION


def _sig(
    signal_type: EvidenceType,
    polarity: EvidencePolarity,
    dim: ProfileDimension = _DIM,
    q_idx: int = 1,
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


# ---- empty -----------------------------------------------------------------

def test_empty_signals_neutral_stats():
    result = EXTRACTOR.analyze([])
    assert result.positive_count == 0
    assert result.negative_count == 0
    assert result.inconsistent_count == 0
    assert result.strength_ratio == 0.5


def test_wrong_dimension_ignored():
    sigs = [
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE, dim=ProfileDimension.TECHNICAL_DEPTH),
        _sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.NEGATIVE, dim=ProfileDimension.ENGINEERING_JUDGMENT),
    ]
    result = EXTRACTOR.analyze(sigs)
    assert result.positive_count == 0
    assert result.negative_count == 0


# ---- positive signals ------------------------------------------------------

def test_repeated_strength_positive_counted():
    sigs = [_sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE)]
    result = EXTRACTOR.analyze(sigs)
    assert result.positive_count == 1


def test_demonstrated_depth_positive_counted():
    sigs = [_sig(EvidenceType.DEMONSTRATED_DEPTH, EvidencePolarity.POSITIVE)]
    result = EXTRACTOR.analyze(sigs)
    assert result.positive_count == 1


def test_positive_type_with_negative_polarity_not_counted():
    sigs = [_sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.NEGATIVE)]
    result = EXTRACTOR.analyze(sigs)
    assert result.positive_count == 0
    assert result.negative_count == 0


# ---- negative signals ------------------------------------------------------

def test_communication_gap_negative_counted():
    sigs = [_sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.NEGATIVE)]
    result = EXTRACTOR.analyze(sigs)
    assert result.negative_count == 1


def test_shallow_answer_negative_counted():
    sigs = [_sig(EvidenceType.SHALLOW_ANSWER, EvidencePolarity.NEGATIVE)]
    result = EXTRACTOR.analyze(sigs)
    assert result.negative_count == 1


def test_negative_type_with_positive_polarity_not_counted():
    sigs = [_sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.POSITIVE)]
    result = EXTRACTOR.analyze(sigs)
    assert result.negative_count == 0


# ---- inconsistent signals --------------------------------------------------

def test_contradictory_answer_counted_as_inconsistent():
    sigs = [_sig(EvidenceType.CONTRADICTORY_ANSWER, EvidencePolarity.NEGATIVE)]
    result = EXTRACTOR.analyze(sigs)
    assert result.inconsistent_count == 1
    assert result.has_inconsistency is True


def test_multiple_contradictory_answers_counted():
    sigs = [
        _sig(EvidenceType.CONTRADICTORY_ANSWER, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.CONTRADICTORY_ANSWER, EvidencePolarity.NEGATIVE),
    ]
    result = EXTRACTOR.analyze(sigs)
    assert result.inconsistent_count == 2


# ---- strength_ratio --------------------------------------------------------

def test_strength_ratio_neutral_no_signals():
    stats = CommunicationStats()
    assert stats.strength_ratio == 0.5


def test_strength_ratio_all_positive():
    stats = CommunicationStats(positive_count=3, negative_count=0)
    assert stats.strength_ratio == 1.0


def test_strength_ratio_all_negative():
    stats = CommunicationStats(positive_count=0, negative_count=3)
    assert stats.strength_ratio == 0.0


def test_strength_ratio_mixed():
    stats = CommunicationStats(positive_count=2, negative_count=2)
    assert stats.strength_ratio == 0.5


def test_strength_ratio_excludes_inconsistent():
    # Inconsistent signals don't affect strength_ratio numerator/denominator
    stats = CommunicationStats(positive_count=2, negative_count=1, inconsistent_count=5)
    assert stats.strength_ratio == pytest.approx(2 / 3)


# ---- total -----------------------------------------------------------------

def test_total_includes_all_categories():
    stats = CommunicationStats(positive_count=2, negative_count=1, inconsistent_count=1)
    assert stats.total == 4


def test_has_inconsistency_false_when_zero():
    stats = CommunicationStats(positive_count=3, negative_count=0, inconsistent_count=0)
    assert stats.has_inconsistency is False
