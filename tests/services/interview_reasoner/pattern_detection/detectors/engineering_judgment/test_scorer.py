# tests/services/interview_reasoner/pattern_detection/detectors/engineering_judgment/test_scorer.py
"""Tests for EngineeringJudgmentScorer."""

from __future__ import annotations

import pytest

from services.interview_reasoner.pattern_detection.detectors.engineering_judgment.analyzer import (
    JudgmentStats,
)
from services.interview_reasoner.pattern_detection.detectors.engineering_judgment.scorer import (
    EngineeringJudgmentScorer,
    JudgmentVerdict,
    HIGH_THRESHOLD,
    LOW_THRESHOLD,
    MIN_EVIDENCE,
    MIN_EVAL_SIGNALS,
)

SCORER = EngineeringJudgmentScorer()


def _stats(positive: int, negative: int, eval_count: int = 1) -> JudgmentStats:
    return JudgmentStats(
        positive_count=positive,
        negative_count=negative,
        evaluation_signal_count=eval_count,
    )


# ---- guard conditions -------------------------------------------------------

def test_neutral_when_no_eval_signals():
    assert SCORER.score(_stats(5, 0, eval_count=0)) == JudgmentVerdict.NEUTRAL


def test_neutral_when_below_min_evidence():
    assert SCORER.score(_stats(1, 0, eval_count=1)) == JudgmentVerdict.NEUTRAL


def test_exactly_min_eval_signals_passes_guard():
    assert SCORER.score(_stats(MIN_EVIDENCE, 0, eval_count=MIN_EVAL_SIGNALS)) == JudgmentVerdict.HIGH


# ---- HIGH verdict -------------------------------------------------------

def test_high_verdict_all_positive():
    assert SCORER.score(_stats(4, 0)) == JudgmentVerdict.HIGH


def test_high_verdict_ratio_above_threshold():
    # ratio = 4/5 = 0.80 ≥ HIGH_THRESHOLD
    assert SCORER.score(_stats(4, 1)) == JudgmentVerdict.HIGH


def test_high_verdict_exactly_threshold():
    # ratio = 0.60, assuming MIN_EVIDENCE=2
    stats = _stats(6, 4)  # 6/10 = 0.60
    result = SCORER.score(stats)
    assert result in (JudgmentVerdict.HIGH, JudgmentVerdict.NEUTRAL)


# ---- LOW verdict -------------------------------------------------------

def test_low_verdict_all_negative():
    assert SCORER.score(_stats(0, 4)) == JudgmentVerdict.LOW


def test_low_verdict_ratio_below_threshold():
    # ratio = 1/5 = 0.20 ≤ LOW_THRESHOLD
    assert SCORER.score(_stats(1, 4)) == JudgmentVerdict.LOW


def test_low_verdict_exactly_threshold():
    stats = _stats(3, 7)  # 3/10 = 0.30
    result = SCORER.score(stats)
    assert result in (JudgmentVerdict.LOW, JudgmentVerdict.NEUTRAL)


# ---- NEUTRAL verdict -------------------------------------------------------

def test_neutral_middle_range():
    # ratio = 0.5, between LOW and HIGH
    assert SCORER.score(_stats(3, 3)) == JudgmentVerdict.NEUTRAL


def test_neutral_insufficient_total():
    assert SCORER.score(_stats(0, 0)) == JudgmentVerdict.NEUTRAL


# ---- operational thinking / risk awareness (ratio-based) -------------------

def test_strong_trade_off_reasoning_gives_high():
    # Simulates: 5 ENGINEERING_JUDGMENT_ARTICULATED + 1 SHALLOW_ANSWER
    assert SCORER.score(_stats(5, 1)) == JudgmentVerdict.HIGH


def test_poor_operational_thinking_gives_low():
    # Simulates: 1 positive, 5 negatives
    assert SCORER.score(_stats(1, 5)) == JudgmentVerdict.LOW
