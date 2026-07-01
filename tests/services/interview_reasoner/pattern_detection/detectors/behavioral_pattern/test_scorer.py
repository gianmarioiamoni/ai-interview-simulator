# tests/services/interview_reasoner/pattern_detection/detectors/behavioral_pattern/test_scorer.py
"""Tests for BehaviorPatternScorer."""

from __future__ import annotations

import pytest

from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern.analyzer import (
    BehavioralStats,
    MIN_ENTRIES,
)
from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern.scorer import (
    BehaviorPatternScorer,
    BehaviorVerdict,
)

SCORER = BehaviorPatternScorer()


def _stats(**kwargs) -> BehavioralStats:
    defaults = dict(
        entry_count=MIN_ENTRIES,
        confidence_trend=0.0,
        positive_ratio=0.5,
        variance_score=0.0,
        has_growth=False,
        has_instability=False,
        has_plateau=False,
    )
    defaults.update(kwargs)
    return BehavioralStats(**defaults)


# ---- guard conditions -------------------------------------------------------

def test_neutral_when_below_min_entries():
    assert SCORER.score(_stats(entry_count=MIN_ENTRIES - 1)) == BehaviorVerdict.NEUTRAL


def test_neutral_exactly_zero_entries():
    assert SCORER.score(_stats(entry_count=0)) == BehaviorVerdict.NEUTRAL


# ---- GROWTH verdict ---------------------------------------------------------

def test_growth_verdict():
    assert SCORER.score(_stats(has_growth=True)) == BehaviorVerdict.GROWTH


def test_growth_takes_precedence_over_plateau():
    assert SCORER.score(_stats(has_growth=True, has_plateau=True)) == BehaviorVerdict.GROWTH


def test_growth_takes_precedence_over_instability():
    assert SCORER.score(_stats(has_growth=True, has_instability=True)) == BehaviorVerdict.GROWTH


# ---- INSTABILITY verdict ----------------------------------------------------

def test_instability_verdict():
    assert SCORER.score(_stats(has_instability=True)) == BehaviorVerdict.INSTABILITY


def test_instability_takes_precedence_over_plateau():
    assert SCORER.score(_stats(has_instability=True, has_plateau=True)) == BehaviorVerdict.INSTABILITY


# ---- PLATEAU verdict --------------------------------------------------------

def test_plateau_verdict():
    assert SCORER.score(_stats(has_plateau=True)) == BehaviorVerdict.PLATEAU


# ---- NEUTRAL verdict --------------------------------------------------------

def test_neutral_when_all_false():
    assert SCORER.score(_stats()) == BehaviorVerdict.NEUTRAL


def test_neutral_sufficient_entries_but_ambiguous():
    assert SCORER.score(_stats(entry_count=5, positive_ratio=0.5)) == BehaviorVerdict.NEUTRAL
