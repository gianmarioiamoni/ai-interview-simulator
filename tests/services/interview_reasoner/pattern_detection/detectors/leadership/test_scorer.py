# tests/services/interview_reasoner/pattern_detection/detectors/leadership/test_scorer.py
"""Tests for LeadershipScorer."""

from __future__ import annotations

import pytest

from services.interview_reasoner.pattern_detection.detectors.leadership.analyzer import (
    LeadershipStats,
)
from services.interview_reasoner.pattern_detection.detectors.leadership.scorer import (
    LeadershipScorer,
    LeadershipVerdict,
    MIN_BEHAVIORAL_SIGNALS,
    MIN_LEADERSHIP_RATIO_STRONG,
    MIN_LEADERSHIP_RATIO_EMERGING,
    MIN_DIMENSIONS_STRONG,
)

SCORER = LeadershipScorer()


def _stats(
    ownership: int = 0,
    initiative: int = 0,
    accountability: int = 0,
    mentoring: int = 0,
    strategic: int = 0,
    total: int = 5,
) -> LeadershipStats:
    return LeadershipStats(
        ownership_signal_count=ownership,
        initiative_signal_count=initiative,
        accountability_signal_count=accountability,
        mentoring_signal_count=mentoring,
        strategic_signal_count=strategic,
        total_behavioral_signals=total,
    )


# ---- guard conditions --------------------------------------------------------

def test_neutral_when_insufficient_signals():
    stats = _stats(ownership=3, initiative=2, total=2)
    assert SCORER.score(stats) == LeadershipVerdict.NEUTRAL


def test_neutral_at_exact_boundary_minus_one():
    stats = _stats(ownership=2, initiative=1, total=MIN_BEHAVIORAL_SIGNALS - 1)
    assert SCORER.score(stats) == LeadershipVerdict.NEUTRAL


# ---- STRONG_LEADER -----------------------------------------------------------

def test_strong_leader_at_threshold():
    # ratio = 6/8 = 0.75 >= 0.60, dims = 3 >= 2
    stats = _stats(ownership=3, initiative=2, accountability=1, total=8)
    assert SCORER.score(stats) == LeadershipVerdict.STRONG_LEADER


def test_strong_leader_exact_ratio_and_dims():
    # ratio = 3/5 = 0.60, dims = ownership+initiative = 2
    stats = _stats(ownership=2, initiative=1, total=5)
    assert SCORER.score(stats) == LeadershipVerdict.STRONG_LEADER


def test_strong_leader_requires_two_dimensions():
    # Only ownership active, ratio = 0.8 but dims = 1 → not STRONG
    stats = _stats(ownership=4, total=5)
    verdict = SCORER.score(stats)
    assert verdict != LeadershipVerdict.STRONG_LEADER


# ---- EMERGING_LEADER ---------------------------------------------------------

def test_emerging_leader_at_threshold():
    # ratio = 2/5 = 0.40 >= 0.35, dims = 1
    stats = _stats(ownership=2, total=5)
    assert SCORER.score(stats) == LeadershipVerdict.EMERGING_LEADER


def test_emerging_leader_exact_ratio():
    # ratio = 0.35, dims = 1
    stats = _stats(ownership=7, total=20)
    assert SCORER.score(stats) == LeadershipVerdict.EMERGING_LEADER


def test_below_emerging_ratio_not_emerging():
    # ratio = 1/5 = 0.2 < 0.35
    stats = _stats(ownership=1, total=5)
    assert SCORER.score(stats) != LeadershipVerdict.EMERGING_LEADER


# ---- LEADERSHIP_ABSENT -------------------------------------------------------

def test_leadership_absent_when_no_leadership_signals():
    # total >= MIN_BEHAVIORAL_SIGNALS, but leadership_score = 0
    stats = LeadershipStats(
        ownership_signal_count=0,
        initiative_signal_count=0,
        accountability_signal_count=0,
        mentoring_signal_count=0,
        strategic_signal_count=0,
        total_behavioral_signals=5,
    )
    assert SCORER.score(stats) == LeadershipVerdict.LEADERSHIP_ABSENT


def test_leadership_absent_only_behavioral_instability():
    # No growth signals → all leadership sub-dims are 0
    stats = LeadershipStats(total_behavioral_signals=5)
    assert SCORER.score(stats) == LeadershipVerdict.LEADERSHIP_ABSENT


# ---- precedence ---------------------------------------------------------------

def test_strong_beats_emerging():
    stats = _stats(ownership=3, initiative=2, accountability=1, total=8)
    assert SCORER.score(stats) == LeadershipVerdict.STRONG_LEADER


def test_emerging_beats_absent():
    stats = _stats(ownership=2, total=5)
    assert SCORER.score(stats) == LeadershipVerdict.EMERGING_LEADER


# ---- determinism -------------------------------------------------------------

def test_same_input_same_output():
    stats = _stats(ownership=3, initiative=2, accountability=1, total=8)
    assert SCORER.score(stats) == SCORER.score(stats)


def test_verdict_enum_values():
    assert LeadershipVerdict.STRONG_LEADER == "STRONG_LEADER"
    assert LeadershipVerdict.EMERGING_LEADER == "EMERGING_LEADER"
    assert LeadershipVerdict.NEUTRAL == "NEUTRAL"
    assert LeadershipVerdict.LEADERSHIP_ABSENT == "LEADERSHIP_ABSENT"
