# tests/services/interview_reasoner/pattern_detection/detectors/test_consistency_across_interview_detector.py
"""Tests for ConsistencyAcrossInterviewDetector (M2-7D, DET-09).

Coverage:
  - Contradictions across distant question areas → CROSS_AREA_CONTRADICTORY
  - Persistent improvement → CROSS_AREA_CONSISTENT
  - Persistent decline → CROSS_AREA_CONTRADICTORY (mixed)
  - Repeated strengths → CROSS_AREA_CONSISTENT
  - Repeated weaknesses → CROSS_AREA_CONSISTENT (negative-consistent)
  - Oscillating behavior → depends on delta
  - Stable interview → CROSS_AREA_CONSISTENT
  - Empty history → no result
  - Idempotency
  - Metadata
  - Label content
"""

from __future__ import annotations

import uuid

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.reasoning.session_metrics import SessionMetrics
from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview_detector import (
    ConsistencyAcrossInterviewDetector,
)

DETECTOR = ConsistencyAcrossInterviewDetector()
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


def _make_input(signals: list[EvidenceSignal], q_idx: int = 5) -> ReasonerInput:
    store = EvidenceStore()
    for s in signals:
        store = store.append(s)
    memory = InterviewMemory(
        evidence_store=store,
        session_metrics=SessionMetrics(questions_answered=q_idx),
    )
    return ReasonerInput(
        session_id="test",
        question_index=q_idx,
        interview_memory=memory,
        current_question_area="concurrency",
    )


P = EvidencePolarity.POSITIVE
N = EvidencePolarity.NEGATIVE


# ---- metadata ---------------------------------------------------------------

def test_metadata_name():
    assert DETECTOR.metadata.name == "ConsistencyAcrossInterviewDetector"


def test_metadata_priority():
    assert DETECTOR.metadata.priority == 80


def test_metadata_depends_on_behavioral():
    assert "BehavioralPatternDetector" in DETECTOR.metadata.dependencies


def test_metadata_version():
    assert DETECTOR.metadata.version == "1.0.0"


# ---- contradiction across distant questions --------------------------------

def test_cross_area_contradiction_detected():
    sigs = [
        _sig(P, "concurrency"), _sig(P, "concurrency"),
        _sig(N, "locking"), _sig(N, "locking"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.CROSS_AREA_CONTRADICTORY in types


def test_contradiction_label_contains_dimension():
    sigs = [
        _sig(P, "concurrency"), _sig(P, "concurrency"),
        _sig(N, "locking"), _sig(N, "locking"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    contradiction_matches = [m for m in result.matches if m.pattern_type == EvidenceType.CROSS_AREA_CONTRADICTORY]
    assert any("technical_depth" in m.label for m in contradiction_matches)


# ---- repeated strengths / consistent ----------------------------------------

def test_repeated_strengths_gives_consistent():
    sigs = [
        _sig(P, "concurrency"), _sig(P, "concurrency"),
        _sig(P, "locking"), _sig(P, "locking"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.CROSS_AREA_CONSISTENT in types


def test_repeated_weaknesses_gives_consistent():
    # Both areas all negative → consistent (negative)
    sigs = [
        _sig(N, "concurrency"), _sig(N, "concurrency"),
        _sig(N, "locking"), _sig(N, "locking"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.CROSS_AREA_CONSISTENT in types


def test_stable_interview_consistent():
    # All areas same ratio → consistent
    sigs = [
        _sig(P, "area_a"), _sig(P, "area_a"), _sig(N, "area_a"),
        _sig(P, "area_b"), _sig(P, "area_b"), _sig(N, "area_b"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.CROSS_AREA_CONSISTENT in types


# ---- persistent improvement -----------------------------------------------

def test_persistent_improvement_across_areas():
    # Both areas strongly positive → consistent
    sigs = [
        _sig(P, "area_a"), _sig(P, "area_a"), _sig(P, "area_a"),
        _sig(P, "area_b"), _sig(P, "area_b"), _sig(P, "area_b"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.CROSS_AREA_CONSISTENT in types


# ---- oscillating behavior --------------------------------------------------

def test_oscillating_behavior_may_be_neutral():
    # Mixed in each area → delta small → could be neutral
    sigs = [
        _sig(P, "area_a"), _sig(N, "area_a"),
        _sig(P, "area_b"), _sig(N, "area_b"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    # Should be consistent (both areas 0.5) or neutral — not contradictory
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.CROSS_AREA_CONTRADICTORY not in types


# ---- empty history ----------------------------------------------------------

def test_empty_signals_no_result():
    result = DETECTOR.detect(_make_input([]))
    assert result.matches == []
    assert result.generated_signals == []


def test_single_area_only_no_result():
    sigs = [_sig(P, "only_area"), _sig(N, "only_area")]
    result = DETECTOR.detect(_make_input(sigs))
    assert result.matches == []


# ---- idempotency -----------------------------------------------------------

def test_idempotency_no_re_emit():
    sigs = [
        _sig(P, "area_a"), _sig(P, "area_a"),
        _sig(N, "area_b"), _sig(N, "area_b"),
    ]
    ri = _make_input(sigs)
    result1 = DETECTOR.detect(ri)
    assert len(result1.generated_signals) > 0

    store = ri.interview_memory.evidence_store
    for s in result1.generated_signals:
        store = store.append(s)
    memory = ri.interview_memory.model_copy(update={"evidence_store": store})
    ri2 = ri.model_copy(update={"interview_memory": memory})
    result2 = DETECTOR.detect(ri2)
    assert len(result2.generated_signals) == 0


# ---- signal contract --------------------------------------------------------

def test_generated_signal_source_is_pattern_detector():
    sigs = [
        _sig(P, "area_a"), _sig(P, "area_a"),
        _sig(N, "area_b"), _sig(N, "area_b"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    for sig in result.generated_signals:
        assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_generated_signal_dimension_matches_finding():
    sigs = [
        _sig(P, "area_a", _DIM), _sig(P, "area_a", _DIM),
        _sig(N, "area_b", _DIM), _sig(N, "area_b", _DIM),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    for sig in result.generated_signals:
        if sig.signal_type == EvidenceType.CROSS_AREA_CONTRADICTORY:
            assert sig.dimension == _DIM


# ---- multiple dimensions ----------------------------------------------------

def test_results_per_dimension():
    sigs = [
        # TECHNICAL_DEPTH: contradiction
        _sig(P, "a", ProfileDimension.TECHNICAL_DEPTH), _sig(P, "a", ProfileDimension.TECHNICAL_DEPTH),
        _sig(N, "b", ProfileDimension.TECHNICAL_DEPTH), _sig(N, "b", ProfileDimension.TECHNICAL_DEPTH),
        # PROBLEM_SOLVING: consistent
        _sig(P, "a", ProfileDimension.PROBLEM_SOLVING), _sig(P, "a", ProfileDimension.PROBLEM_SOLVING),
        _sig(P, "b", ProfileDimension.PROBLEM_SOLVING), _sig(P, "b", ProfileDimension.PROBLEM_SOLVING),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.CROSS_AREA_CONTRADICTORY in types
    assert EvidenceType.CROSS_AREA_CONSISTENT in types
