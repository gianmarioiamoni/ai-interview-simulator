# tests/services/interview_reasoner/pattern_detection/detectors/collaboration/test_scorer.py
"""Tests for CollaborationScorer."""

from __future__ import annotations

import pytest

from services.interview_reasoner.pattern_detection.detectors.collaboration.analyzer import (
    CollaborationStats,
)
from services.interview_reasoner.pattern_detection.detectors.collaboration.scorer import (
    CollaborationScorer,
    CollaborationVerdict,
    MIN_BEHAVIORAL_SIGNALS,
    MIN_COLLAB_RATIO_STRONG,
    MIN_COLLAB_RATIO_EFFECTIVE,
    MIN_CONFLICT_RESOLUTION_STRONG,
    MIN_CROSS_FUNCTIONAL_EFFECTIVE,
)

SCORER = CollaborationScorer()


def _stats(
    team: int = 0,
    sharing: int = 0,
    feedback: int = 0,
    cross_func: int = 0,
    conflict_total: int = 0,
    conflict_pos: int = 0,
    total: int = 5,
) -> CollaborationStats:
    return CollaborationStats(
        team_orientation_count=team,
        knowledge_sharing_count=sharing,
        feedback_acceptance_count=feedback,
        cross_functional_count=cross_func,
        conflict_signals_count=conflict_total,
        positive_conflict_count=conflict_pos,
        total_behavioral_signals=total,
    )


# ---- guard conditions --------------------------------------------------------

def test_neutral_when_insufficient_signals():
    stats = _stats(team=3, sharing=2, total=2)
    assert SCORER.score(stats) == CollaborationVerdict.NEUTRAL


def test_neutral_at_boundary_minus_one():
    stats = _stats(team=2, total=MIN_BEHAVIORAL_SIGNALS - 1)
    assert SCORER.score(stats) == CollaborationVerdict.NEUTRAL


# ---- STRONG_COLLABORATOR -----------------------------------------------------

def test_strong_collaborator_at_threshold():
    # ratio = (3+2+1)/10 = 0.6 >= 0.55; conflict_res = 1.0 >= 0.60 (no conflict)
    stats = _stats(team=3, sharing=2, feedback=1, total=10)
    assert SCORER.score(stats) == CollaborationVerdict.STRONG_COLLABORATOR


def test_strong_collaborator_exact_ratio():
    # ratio = (3+1+1)/9 = 0.555..., conflict_res = 1.0
    stats = _stats(team=3, sharing=1, feedback=1, total=9)
    assert SCORER.score(stats) == CollaborationVerdict.STRONG_COLLABORATOR


def test_strong_requires_good_conflict_resolution():
    # ratio = 0.6 but conflict_res = 0.4 < 0.60 → NOT STRONG
    stats = _stats(team=3, sharing=2, feedback=1, conflict_total=5, conflict_pos=2, total=10)
    verdict = SCORER.score(stats)
    assert verdict != CollaborationVerdict.STRONG_COLLABORATOR


def test_strong_requires_sufficient_ratio():
    # conflict_res = 1.0 but ratio too low → not STRONG
    stats = _stats(team=1, total=10)
    verdict = SCORER.score(stats)
    assert verdict != CollaborationVerdict.STRONG_COLLABORATOR


# ---- EFFECTIVE_COLLABORATOR --------------------------------------------------

def test_effective_collaborator_by_ratio():
    # ratio = 2/5 = 0.40 >= 0.30
    stats = _stats(team=2, total=5)
    assert SCORER.score(stats) == CollaborationVerdict.EFFECTIVE_COLLABORATOR


def test_effective_collaborator_by_cross_functional():
    # ratio low but cross_func = 2 >= 2
    stats = _stats(cross_func=2, total=5)
    assert SCORER.score(stats) == CollaborationVerdict.EFFECTIVE_COLLABORATOR


def test_below_effective_ratio_not_effective():
    # ratio = 1/8 = 0.125 < 0.30 and cross_func = 0
    stats = _stats(team=1, total=8)
    assert SCORER.score(stats) != CollaborationVerdict.EFFECTIVE_COLLABORATOR


# ---- COLLABORATION_DEFICIT ---------------------------------------------------

def test_collaboration_deficit_when_no_collab_signals():
    stats = CollaborationStats(total_behavioral_signals=5)
    assert SCORER.score(stats) == CollaborationVerdict.COLLABORATION_DEFICIT


def test_collaboration_deficit_only_instability():
    stats = CollaborationStats(
        conflict_signals_count=5,
        total_behavioral_signals=5,
    )
    assert SCORER.score(stats) == CollaborationVerdict.COLLABORATION_DEFICIT


# ---- verdict precedence -------------------------------------------------------

def test_strong_beats_effective():
    stats = _stats(team=3, sharing=2, feedback=1, total=10)
    assert SCORER.score(stats) == CollaborationVerdict.STRONG_COLLABORATOR


def test_effective_beats_deficit():
    stats = _stats(team=2, total=5)
    assert SCORER.score(stats) == CollaborationVerdict.EFFECTIVE_COLLABORATOR


# ---- determinism -------------------------------------------------------------

def test_same_input_same_output():
    stats = _stats(team=3, sharing=2, feedback=1, total=10)
    assert SCORER.score(stats) == SCORER.score(stats)


def test_verdict_enum_values():
    assert CollaborationVerdict.STRONG_COLLABORATOR == "STRONG_COLLABORATOR"
    assert CollaborationVerdict.EFFECTIVE_COLLABORATOR == "EFFECTIVE_COLLABORATOR"
    assert CollaborationVerdict.NEUTRAL == "NEUTRAL"
    assert CollaborationVerdict.COLLABORATION_DEFICIT == "COLLABORATION_DEFICIT"
