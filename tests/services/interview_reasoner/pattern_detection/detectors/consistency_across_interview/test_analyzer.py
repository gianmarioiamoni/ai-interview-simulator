# tests/services/interview_reasoner/pattern_detection/detectors/consistency_across_interview/test_analyzer.py
"""Tests for ConsistencyHistoryAnalyzer."""

from __future__ import annotations

import uuid

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview.analyzer import (
    ConsistencyHistoryAnalyzer,
    CONTRADICTION_THRESHOLD,
    CONSISTENCY_THRESHOLD,
    MIN_SIGNALS_PER_AREA,
)

ANALYZER = ConsistencyHistoryAnalyzer()
_DIM = ProfileDimension.TECHNICAL_DEPTH


def _sig(
    polarity: EvidencePolarity,
    area: str,
    dim: ProfileDimension = _DIM,
    q_idx: int = 1,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=q_idx,
        question_area=area,
        dimension=dim,
        polarity=polarity,
        signal_type=EvidenceType.DEMONSTRATED_DEPTH,
        strength=0.7,
        source=EvidenceSource.EVALUATION,
        timestamp_question_index=q_idx,
    )


P = EvidencePolarity.POSITIVE
N = EvidencePolarity.NEGATIVE


# ---- empty / insufficient --------------------------------------------------

def test_empty_signals_returns_empty():
    result = ANALYZER.analyze([])
    assert result == []


def test_single_area_insufficient_no_result():
    sigs = [_sig(P, "area_a"), _sig(P, "area_a")]
    result = ANALYZER.analyze(sigs)
    assert result == []


def test_two_areas_below_min_signals_per_area_skipped():
    # Each area has only 1 signal — below MIN_SIGNALS_PER_AREA
    sigs = [_sig(P, "area_a"), _sig(N, "area_b")]
    result = ANALYZER.analyze(sigs)
    assert result == []


# ---- contradiction detection -----------------------------------------------

def test_contradiction_opposite_polarity_areas():
    # area_a: all positive, area_b: all negative → delta = 1.0
    sigs = [
        _sig(P, "area_a"), _sig(P, "area_a"),
        _sig(N, "area_b"), _sig(N, "area_b"),
    ]
    result = ANALYZER.analyze(sigs)
    assert len(result) == 1
    assert result[0].has_contradiction is True
    assert result[0].max_ratio_delta == pytest.approx(1.0)


def test_contradiction_areas_in_label():
    sigs = [
        _sig(P, "concurrency"), _sig(P, "concurrency"),
        _sig(N, "locking"), _sig(N, "locking"),
    ]
    result = ANALYZER.analyze(sigs)
    assert len(result) == 1
    r = result[0]
    assert "concurrency" in r.contradictory_areas or "locking" in r.contradictory_areas


def test_contradiction_threshold_boundary():
    # delta = CONTRADICTION_THRESHOLD exactly → has_contradiction
    # area_a: 6 pos, 4 neg → ratio=0.6
    # area_b: 4 pos, 6 neg → ratio=0.4 → delta=0.2 < 0.4 → no contradiction
    sigs = (
        [_sig(P, "a")] * 6 + [_sig(N, "a")] * 4 +
        [_sig(P, "b")] * 4 + [_sig(N, "b")] * 6
    )
    result = ANALYZER.analyze(sigs)
    assert len(result) == 1
    assert result[0].has_contradiction is False


# ---- consistency detection -------------------------------------------------

def test_consistent_areas_same_polarity():
    sigs = [
        _sig(P, "area_a"), _sig(P, "area_a"),
        _sig(P, "area_b"), _sig(P, "area_b"),
    ]
    result = ANALYZER.analyze(sigs)
    assert len(result) == 1
    assert result[0].has_consistency is True
    assert result[0].has_contradiction is False


def test_consistent_near_zero_delta():
    # Both areas: 3 pos, 1 neg → ratio=0.75, delta=0.0 → consistent
    sigs = (
        [_sig(P, "a")] * 3 + [_sig(N, "a")] +
        [_sig(P, "b")] * 3 + [_sig(N, "b")]
    )
    result = ANALYZER.analyze(sigs)
    assert result[0].has_consistency is True


# ---- multiple dimensions ---------------------------------------------------

def test_multiple_dimensions_analyzed_independently():
    sigs = [
        # TECHNICAL_DEPTH: contradictory
        _sig(P, "area_a", ProfileDimension.TECHNICAL_DEPTH), _sig(P, "area_a", ProfileDimension.TECHNICAL_DEPTH),
        _sig(N, "area_b", ProfileDimension.TECHNICAL_DEPTH), _sig(N, "area_b", ProfileDimension.TECHNICAL_DEPTH),
        # PROBLEM_SOLVING: consistent
        _sig(P, "area_a", ProfileDimension.PROBLEM_SOLVING), _sig(P, "area_a", ProfileDimension.PROBLEM_SOLVING),
        _sig(P, "area_b", ProfileDimension.PROBLEM_SOLVING), _sig(P, "area_b", ProfileDimension.PROBLEM_SOLVING),
    ]
    result = ANALYZER.analyze(sigs)
    dims = {r.dimension for r in result}
    assert ProfileDimension.TECHNICAL_DEPTH in dims
    assert ProfileDimension.PROBLEM_SOLVING in dims

    td = next(r for r in result if r.dimension == ProfileDimension.TECHNICAL_DEPTH)
    ps = next(r for r in result if r.dimension == ProfileDimension.PROBLEM_SOLVING)
    assert td.has_contradiction is True
    assert ps.has_consistency is True


# ---- max_ratio_delta --------------------------------------------------------

def test_max_delta_computed_correctly():
    # area_a: 4/4 = 1.0, area_b: 0/4 = 0.0, area_c: 2/4 = 0.5
    # max delta = 1.0 - 0.0 = 1.0
    sigs = (
        [_sig(P, "a")] * 4 +
        [_sig(N, "b")] * 4 +
        [_sig(P, "c")] * 2 + [_sig(N, "c")] * 2
    )
    result = ANALYZER.analyze(sigs)
    assert len(result) == 1
    assert result[0].max_ratio_delta == pytest.approx(1.0)
