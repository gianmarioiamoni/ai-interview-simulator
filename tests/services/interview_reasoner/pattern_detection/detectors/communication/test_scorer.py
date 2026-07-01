# tests/services/interview_reasoner/pattern_detection/detectors/communication/test_scorer.py
"""Tests for CommunicationScorer."""

from __future__ import annotations

import pytest

from services.interview_reasoner.pattern_detection.detectors.communication.analyzer import (
    CommunicationStats,
)
from services.interview_reasoner.pattern_detection.detectors.communication.scorer import (
    CommunicationScorer,
    CommunicationVerdict,
    CLEAR_THRESHOLD,
    WEAK_THRESHOLD,
    MIN_EVIDENCE,
)

SCORER = CommunicationScorer()


def _stats(positive: int, negative: int, inconsistent: int = 0) -> CommunicationStats:
    return CommunicationStats(
        positive_count=positive,
        negative_count=negative,
        inconsistent_count=inconsistent,
    )


# ---- guard: MIN_EVIDENCE ---------------------------------------------------

def test_neutral_when_below_min_evidence():
    assert SCORER.score(_stats(1, 0)) == CommunicationVerdict.NEUTRAL


def test_exactly_min_evidence_passes():
    # 2 positive, 0 negative → CLEAR
    result = SCORER.score(_stats(MIN_EVIDENCE, 0))
    assert result == CommunicationVerdict.CLEAR


def test_zero_signals_neutral():
    assert SCORER.score(_stats(0, 0)) == CommunicationVerdict.NEUTRAL


# ---- CLEAR verdict ---------------------------------------------------------

def test_clear_verdict_all_positive():
    assert SCORER.score(_stats(4, 0)) == CommunicationVerdict.CLEAR


def test_clear_verdict_ratio_above_threshold():
    # ratio = 4/5 = 0.80 ≥ CLEAR_THRESHOLD
    assert SCORER.score(_stats(4, 1)) == CommunicationVerdict.CLEAR


def test_clear_verdict_boundary():
    # ratio exactly at CLEAR_THRESHOLD (may be CLEAR or NEUTRAL)
    n = 20
    pos = int(CLEAR_THRESHOLD * n)
    neg = n - pos
    result = SCORER.score(_stats(pos, neg))
    assert result in (CommunicationVerdict.CLEAR, CommunicationVerdict.NEUTRAL)


# ---- WEAK verdict ----------------------------------------------------------

def test_weak_verdict_all_negative():
    assert SCORER.score(_stats(0, 4)) == CommunicationVerdict.WEAK


def test_weak_verdict_persistent_weakness():
    # ratio = 1/5 = 0.20 ≤ WEAK_THRESHOLD
    assert SCORER.score(_stats(1, 4)) == CommunicationVerdict.WEAK


def test_verbosity_poor_structure_gives_weak():
    # Simulates: 5 COMMUNICATION_GAP + 1 positive
    assert SCORER.score(_stats(1, 5)) == CommunicationVerdict.WEAK


# ---- INCONSISTENT verdict --------------------------------------------------

def test_inconsistent_verdict_takes_precedence():
    # Even with high positive ratio, inconsistency wins
    assert SCORER.score(_stats(4, 1, inconsistent=1)) == CommunicationVerdict.INCONSISTENT


def test_inconsistent_verdict_only_inconsistent_signals():
    # total = inconsistent_count only; needs ≥ MIN_EVIDENCE
    assert SCORER.score(_stats(0, 0, inconsistent=3)) == CommunicationVerdict.INCONSISTENT


def test_inconsistent_single_signal_with_others():
    assert SCORER.score(_stats(2, 1, inconsistent=1)) == CommunicationVerdict.INCONSISTENT


# ---- NEUTRAL verdict -------------------------------------------------------

def test_neutral_middle_range():
    # ratio = 0.5, between WEAK and CLEAR thresholds
    assert SCORER.score(_stats(3, 3)) == CommunicationVerdict.NEUTRAL


def test_neutral_no_inconsistency_middle_ratio():
    assert SCORER.score(_stats(2, 2)) == CommunicationVerdict.NEUTRAL


# ---- logical progression ---------------------------------------------------

def test_clear_structure_gives_clear():
    # Simulates good logical flow: 3 REPEATED_STRENGTH + 1 COMMUNICATION_GAP
    assert SCORER.score(_stats(3, 1)) == CommunicationVerdict.CLEAR


def test_conciseness_pattern_clear():
    assert SCORER.score(_stats(5, 1)) == CommunicationVerdict.CLEAR
