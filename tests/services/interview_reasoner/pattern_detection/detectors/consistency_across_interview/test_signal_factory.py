# tests/services/interview_reasoner/pattern_detection/detectors/consistency_across_interview/test_signal_factory.py
"""Tests for ConsistencySignalFactory."""

from __future__ import annotations

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview.analyzer import (
    CrossAreaResult,
)
from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview.scorer import (
    ConsistencyVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview.signal_factory import (
    ConsistencySignalFactory,
)

FACTORY = ConsistencySignalFactory()
_DIM = ProfileDimension.TECHNICAL_DEPTH


def _result(contradiction: bool = False, consistency: bool = False, delta: float = 0.0) -> CrossAreaResult:
    return CrossAreaResult(
        dimension=_DIM,
        has_contradiction=contradiction,
        has_consistency=consistency,
        contradictory_areas=("area_a", "area_b"),
        max_ratio_delta=delta,
    )


def test_contradictory_produces_negative_signal():
    sig = FACTORY.make_signal(ConsistencyVerdict.CONTRADICTORY, _result(contradiction=True, delta=0.6), 3, "area")
    assert sig is not None
    assert sig.signal_type == EvidenceType.CROSS_AREA_CONTRADICTORY
    assert sig.polarity == EvidencePolarity.NEGATIVE
    assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_consistent_produces_positive_signal():
    sig = FACTORY.make_signal(ConsistencyVerdict.CONSISTENT, _result(consistency=True, delta=0.1), 3, "area")
    assert sig is not None
    assert sig.signal_type == EvidenceType.CROSS_AREA_CONSISTENT
    assert sig.polarity == EvidencePolarity.POSITIVE
    assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_neutral_returns_none():
    sig = FACTORY.make_signal(ConsistencyVerdict.NEUTRAL, _result(), 3, "area")
    assert sig is None


def test_contradictory_strength_from_delta():
    sig = FACTORY.make_signal(ConsistencyVerdict.CONTRADICTORY, _result(contradiction=True, delta=0.7), 1, "area")
    assert sig is not None
    assert sig.strength == pytest.approx(0.7)


def test_consistent_strength_inverted():
    sig = FACTORY.make_signal(ConsistencyVerdict.CONSISTENT, _result(consistency=True, delta=0.1), 1, "area")
    assert sig is not None
    assert sig.strength == pytest.approx(0.9)


def test_signal_dimension_matches_result():
    sig = FACTORY.make_signal(ConsistencyVerdict.CONTRADICTORY, _result(contradiction=True), 1, "area")
    assert sig is not None
    assert sig.dimension == _DIM


def test_question_index_set():
    sig = FACTORY.make_signal(ConsistencyVerdict.CONTRADICTORY, _result(contradiction=True), 5, "area")
    assert sig is not None
    assert sig.question_index == 5
    assert sig.timestamp_question_index == 5


def test_unique_ids():
    r = _result(contradiction=True)
    s1 = FACTORY.make_signal(ConsistencyVerdict.CONTRADICTORY, r, 1, "area")
    s2 = FACTORY.make_signal(ConsistencyVerdict.CONTRADICTORY, r, 1, "area")
    assert s1 is not None and s2 is not None
    assert s1.id != s2.id
