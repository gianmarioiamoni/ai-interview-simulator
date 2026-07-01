# tests/services/interview_reasoner/pattern_detection/detectors/behavioral_pattern/test_analyzer.py
"""Tests for BehaviorObservationExtractor."""

from __future__ import annotations

import pytest

from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.reasoning_history import ReasoningEntry
from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern.analyzer import (
    BehaviorObservationExtractor,
    BehavioralStats,
    MIN_ENTRIES,
    POSITIVE_PATTERN_TYPES,
    NEGATIVE_PATTERN_TYPES,
)

EXTRACTOR = BehaviorObservationExtractor()


def _entry(
    q_idx: int = 0,
    confidence: float = 0.6,
    patterns: list[EvidenceType] | None = None,
) -> ReasoningEntry:
    return ReasoningEntry(
        question_index=q_idx,
        reasoning_confidence=confidence,
        detected_patterns=patterns or [],
    )


# ---- empty / insufficient entries -----------------------------------------

def test_empty_entries_returns_neutral_stats():
    result = EXTRACTOR.analyze([])
    assert result.entry_count == 0
    assert result.has_growth is False
    assert result.has_instability is False
    assert result.has_plateau is False


def test_below_min_entries_returns_neutral():
    entries = [_entry(i, 0.5) for i in range(MIN_ENTRIES - 1)]
    result = EXTRACTOR.analyze(entries)
    assert result.entry_count == MIN_ENTRIES - 1
    assert result.has_growth is False
    assert result.has_instability is False


def test_exactly_min_entries_processes():
    entries = [_entry(i, 0.5 + i * 0.1) for i in range(MIN_ENTRIES)]
    result = EXTRACTOR.analyze(entries)
    assert result.entry_count == MIN_ENTRIES


# ---- confidence trend -------------------------------------------------------

def test_growing_confidence_detected():
    entries = [
        _entry(0, 0.3),
        _entry(1, 0.5),
        _entry(2, 0.7),
        _entry(3, 0.9),
    ]
    result = EXTRACTOR.analyze(entries)
    assert result.confidence_trend > 0


def test_declining_confidence_detected():
    entries = [
        _entry(0, 0.9),
        _entry(1, 0.7),
        _entry(2, 0.5),
        _entry(3, 0.3),
    ]
    result = EXTRACTOR.analyze(entries)
    assert result.confidence_trend < 0


def test_stable_confidence_near_zero_trend():
    entries = [_entry(i, 0.6) for i in range(4)]
    result = EXTRACTOR.analyze(entries)
    assert abs(result.confidence_trend) <= 0.05


# ---- growth detection -------------------------------------------------------

def test_has_growth_with_improving_confidence_and_positive_patterns():
    pos = EvidenceType.REPEATED_STRENGTH
    entries = [
        _entry(0, 0.3, [pos]),
        _entry(1, 0.5, [pos]),
        _entry(2, 0.7, [pos]),
        _entry(3, 0.9, [pos]),
    ]
    result = EXTRACTOR.analyze(entries)
    assert result.has_growth is True


def test_no_growth_when_confidence_flat():
    pos = EvidenceType.REPEATED_STRENGTH
    entries = [_entry(i, 0.6, [pos]) for i in range(4)]
    result = EXTRACTOR.analyze(entries)
    assert result.has_growth is False


def test_no_growth_when_low_positive_ratio():
    neg = EvidenceType.SHALLOW_ANSWER
    entries = [
        _entry(0, 0.3, [neg]),
        _entry(1, 0.5, [neg]),
        _entry(2, 0.7, [neg]),
        _entry(3, 0.9, [neg]),
    ]
    result = EXTRACTOR.analyze(entries)
    assert result.has_growth is False


# ---- instability detection --------------------------------------------------

def test_has_instability_with_high_pattern_variance():
    # Alternating completely different patterns → high Jaccard dissimilarity
    entries = [
        _entry(0, 0.6, [EvidenceType.REPEATED_STRENGTH]),
        _entry(1, 0.6, [EvidenceType.SHALLOW_ANSWER]),
        _entry(2, 0.6, [EvidenceType.DEMONSTRATED_DEPTH]),
        _entry(3, 0.6, [EvidenceType.REASONING_GAP]),
    ]
    result = EXTRACTOR.analyze(entries)
    assert result.has_instability is True


def test_no_instability_with_stable_patterns():
    same = [EvidenceType.REPEATED_STRENGTH]
    entries = [_entry(i, 0.6, same) for i in range(4)]
    result = EXTRACTOR.analyze(entries)
    assert result.has_instability is False


# ---- plateau detection ------------------------------------------------------

def test_has_plateau_stable_confidence_no_instability():
    same = [EvidenceType.REPEATED_STRENGTH]
    entries = [_entry(i, 0.6, same) for i in range(4)]
    result = EXTRACTOR.analyze(entries)
    assert result.has_plateau is True


def test_no_plateau_when_growing():
    pos = EvidenceType.REPEATED_STRENGTH
    entries = [
        _entry(0, 0.3, [pos]),
        _entry(1, 0.5, [pos]),
        _entry(2, 0.7, [pos]),
        _entry(3, 0.9, [pos]),
    ]
    result = EXTRACTOR.analyze(entries)
    assert result.has_plateau is False


# ---- positive_ratio ---------------------------------------------------------

def test_positive_ratio_all_positive():
    pos = EvidenceType.REPEATED_STRENGTH
    entries = [_entry(i, 0.6, [pos]) for i in range(4)]
    result = EXTRACTOR.analyze(entries)
    assert result.positive_ratio == pytest.approx(1.0)


def test_positive_ratio_all_negative():
    neg = EvidenceType.SHALLOW_ANSWER
    entries = [_entry(i, 0.6, [neg]) for i in range(4)]
    result = EXTRACTOR.analyze(entries)
    assert result.positive_ratio == pytest.approx(0.0)


def test_positive_ratio_mixed():
    entries = [
        _entry(0, 0.6, [EvidenceType.REPEATED_STRENGTH]),
        _entry(1, 0.6, [EvidenceType.SHALLOW_ANSWER]),
        _entry(2, 0.6, [EvidenceType.DEMONSTRATED_DEPTH]),
        _entry(3, 0.6, [EvidenceType.REASONING_GAP]),
    ]
    result = EXTRACTOR.analyze(entries)
    assert 0.0 < result.positive_ratio < 1.0


# ---- no patterns (empty) ---------------------------------------------------

def test_entries_with_no_patterns():
    entries = [_entry(i, 0.6, []) for i in range(4)]
    result = EXTRACTOR.analyze(entries)
    assert result.entry_count == 4
    assert result.positive_ratio == pytest.approx(0.0)
