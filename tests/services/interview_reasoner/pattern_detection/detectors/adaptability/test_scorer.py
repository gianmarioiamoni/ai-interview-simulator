# tests/services/interview_reasoner/pattern_detection/detectors/adaptability/test_scorer.py
"""Tests for AdaptabilityScorer."""

from __future__ import annotations

import pytest

from services.interview_reasoner.pattern_detection.detectors.adaptability.analyzer import (
    AdaptabilityStats,
)
from services.interview_reasoner.pattern_detection.detectors.adaptability.scorer import (
    AdaptabilityScorer,
    AdaptabilityVerdict,
    MIN_INSTABILITY_EVENTS,
    MIN_ADAPTABILITY_RATIO_HIGH,
    MIN_ADAPTABILITY_RATIO_ADAPTABLE,
    MIN_FLEXIBILITY_RATIO_ADAPTABLE,
    LOW_ADAPTABILITY_RIGIDITY_FLOOR,
)

SCORER = AdaptabilityScorer()


def _stats(
    recovery: int = 0,
    rigidity: int = 0,
    flexibility: int = 0,
    context_switch: int = 1,
    total_instability: int = 0,
    total_behavioral: int = 5,
    reframing: int = 0,
) -> AdaptabilityStats:
    return AdaptabilityStats(
        recovery_count=recovery,
        rigidity_count=rigidity,
        flexibility_count=flexibility,
        context_switch_count=context_switch,
        reframing_events=reframing,
        total_instability_events=total_instability,
        total_behavioral_signals=total_behavioral,
    )


# ---- guard conditions --------------------------------------------------------

def test_neutral_when_no_instability_and_low_flexibility():
    stats = _stats(total_instability=0, flexibility=0)
    assert SCORER.score(stats) == AdaptabilityVerdict.NEUTRAL


def test_neutral_when_below_min_instability_no_flexibility():
    stats = _stats(total_instability=MIN_INSTABILITY_EVENTS - 1, flexibility=2)
    assert SCORER.score(stats) == AdaptabilityVerdict.NEUTRAL


# ---- special proactive flexibility path -------------------------------------

def test_adaptable_when_no_instability_and_high_flexibility():
    stats = _stats(total_instability=0, flexibility=3)
    assert SCORER.score(stats) == AdaptabilityVerdict.ADAPTABLE


def test_not_highly_adaptable_via_proactive_path():
    stats = _stats(total_instability=0, flexibility=5)
    assert SCORER.score(stats) == AdaptabilityVerdict.ADAPTABLE


# ---- HIGHLY_ADAPTABLE --------------------------------------------------------

def test_highly_adaptable_at_threshold():
    # ratio = 7/10 = 0.70, trend not DECLINING (3 recoveries > 3 rigid → IMPROVING)
    stats = _stats(recovery=7, rigidity=3, flexibility=2, total_instability=10, context_switch=4)
    assert SCORER.score(stats) == AdaptabilityVerdict.HIGHLY_ADAPTABLE


def test_highly_adaptable_requires_non_declining_trend():
    # ratio >= 0.70 but rigidity > recovery → DECLINING
    stats = _stats(recovery=7, rigidity=10, flexibility=0, total_instability=10, context_switch=1)
    verdict = SCORER.score(stats)
    assert verdict != AdaptabilityVerdict.HIGHLY_ADAPTABLE


def test_highly_adaptable_full_recovery():
    stats = _stats(recovery=5, rigidity=0, flexibility=3, total_instability=5, context_switch=4)
    assert SCORER.score(stats) == AdaptabilityVerdict.HIGHLY_ADAPTABLE


# ---- ADAPTABLE ---------------------------------------------------------------

def test_adaptable_by_ratio():
    # ratio = 2/5 = 0.40, flex_ratio = 0/1 = 0
    stats = _stats(recovery=2, rigidity=3, total_instability=5, flexibility=0)
    assert SCORER.score(stats) == AdaptabilityVerdict.ADAPTABLE


def test_adaptable_by_flexibility_ratio():
    # flex = 2/context=2 → flex_ratio = 1.0 >= 0.5, ratio low
    stats = _stats(recovery=1, rigidity=2, total_instability=3, flexibility=2, context_switch=2)
    assert SCORER.score(stats) == AdaptabilityVerdict.ADAPTABLE


# ---- LOW_ADAPTABILITY --------------------------------------------------------

def test_low_adaptability_rigidity_dominates():
    # rigidity=3 > recovery=1 and rigidity >= 2
    stats = _stats(recovery=1, rigidity=3, total_instability=4, flexibility=0)
    assert SCORER.score(stats) == AdaptabilityVerdict.LOW_ADAPTABILITY


def test_low_adaptability_at_floor():
    # rigidity=2 >= 2, recovery=0
    stats = _stats(recovery=0, rigidity=2, total_instability=2, flexibility=0)
    assert SCORER.score(stats) == AdaptabilityVerdict.LOW_ADAPTABILITY


def test_not_low_adaptability_when_rigidity_below_floor():
    # rigidity=1 < 2
    stats = _stats(recovery=0, rigidity=1, total_instability=1, flexibility=0)
    # Below guard or neutral
    verdict = SCORER.score(stats)
    assert verdict != AdaptabilityVerdict.LOW_ADAPTABILITY


# ---- precedence --------------------------------------------------------------

def test_highly_adaptable_beats_adaptable():
    stats = _stats(recovery=7, rigidity=3, flexibility=2, total_instability=10, context_switch=4)
    assert SCORER.score(stats) == AdaptabilityVerdict.HIGHLY_ADAPTABLE


def test_adaptable_beats_low():
    stats = _stats(recovery=2, rigidity=3, total_instability=5, flexibility=0)
    assert SCORER.score(stats) == AdaptabilityVerdict.ADAPTABLE


# ---- determinism -------------------------------------------------------------

def test_same_input_same_output():
    stats = _stats(recovery=7, rigidity=3, flexibility=2, total_instability=10, context_switch=4)
    assert SCORER.score(stats) == SCORER.score(stats)


def test_verdict_enum_values():
    assert AdaptabilityVerdict.HIGHLY_ADAPTABLE == "HIGHLY_ADAPTABLE"
    assert AdaptabilityVerdict.ADAPTABLE == "ADAPTABLE"
    assert AdaptabilityVerdict.NEUTRAL == "NEUTRAL"
    assert AdaptabilityVerdict.LOW_ADAPTABILITY == "LOW_ADAPTABILITY"
