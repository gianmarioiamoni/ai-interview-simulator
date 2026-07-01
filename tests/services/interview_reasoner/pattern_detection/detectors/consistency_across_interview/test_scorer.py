# tests/services/interview_reasoner/pattern_detection/detectors/consistency_across_interview/test_scorer.py
"""Tests for ConsistencyScorer."""

from __future__ import annotations

from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview.analyzer import (
    CrossAreaResult,
)
from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview.scorer import (
    ConsistencyScorer,
    ConsistencyVerdict,
)

SCORER = ConsistencyScorer()
_DIM = ProfileDimension.TECHNICAL_DEPTH


def _result(**kwargs) -> CrossAreaResult:
    defaults = dict(
        dimension=_DIM,
        has_contradiction=False,
        has_consistency=False,
        contradictory_areas=("", ""),
        max_ratio_delta=0.0,
    )
    defaults.update(kwargs)
    return CrossAreaResult(**defaults)


def test_contradictory_verdict():
    assert SCORER.score(_result(has_contradiction=True)) == ConsistencyVerdict.CONTRADICTORY


def test_consistent_verdict():
    assert SCORER.score(_result(has_consistency=True)) == ConsistencyVerdict.CONSISTENT


def test_neutral_when_neither():
    assert SCORER.score(_result()) == ConsistencyVerdict.NEUTRAL


def test_contradictory_takes_precedence():
    # Even if has_consistency somehow True, contradiction wins
    assert SCORER.score(_result(has_contradiction=True, has_consistency=True)) == ConsistencyVerdict.CONTRADICTORY


def test_neutral_both_false():
    assert SCORER.score(_result(has_contradiction=False, has_consistency=False)) == ConsistencyVerdict.NEUTRAL
