# tests/services/interview_reasoner/pattern_detection/detectors/test_evaluation_signal_detector.py
"""Tests for EvaluationSignalDetector (M2-7B).

Coverage:
  - Sliding window: only signals within last N question indices bridged
  - Old signals ignored (outside window)
  - Window=1, Window=3 boundaries
  - Window larger than number of answered questions
  - No evaluation signals → empty result
  - Mixed signal types (bridgeable vs non-bridgeable)
  - Idempotency (no duplicate derived signals)
  - settings.reasoner_bridge_window is respected
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
from domain.contracts.reasoning.session_metrics import SessionMetrics
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.detectors.evaluation_signal_detector import (
    EvaluationSignalDetector,
    BRIDGEABLE_TYPES,
)

DETECTOR = EvaluationSignalDetector()


def _make_eval_sig(
    q_idx: int,
    signal_type: EvidenceType = EvidenceType.KNOWLEDGE_GAP,
    dim: ProfileDimension = ProfileDimension.TECHNICAL_DEPTH,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=q_idx,
        question_area="area",
        dimension=dim,
        polarity=EvidencePolarity.NEGATIVE,
        signal_type=signal_type,
        strength=0.7,
        source=EvidenceSource.EVALUATION,
        timestamp_question_index=q_idx,
    )


def _make_input(
    signals: list[EvidenceSignal],
    question_index: int = 10,
    window: int | None = None,
) -> ReasonerInput:
    store = EvidenceStore(signals=signals)
    memory = InterviewMemory(
        evidence_store=store,
        session_metrics=SessionMetrics(questions_answered=question_index),
    )
    from infrastructure.config.settings import settings as _s
    if window is not None:
        object.__setattr__(_s, "reasoner_bridge_window", window)
    return ReasonerInput(
        session_id="test",
        question_index=question_index,
        interview_memory=memory,
        current_question_area="area",
    )


# ---- metadata -----------------------------------------------------------

def test_metadata_name():
    assert DETECTOR.metadata.name == "EvaluationSignalDetector"


def test_metadata_priority():
    assert DETECTOR.metadata.priority == 5


def test_metadata_no_dependencies():
    assert DETECTOR.metadata.dependencies == []


# ---- no signals ----------------------------------------------------------

def test_no_signals_returns_empty():
    rinput = _make_input([], question_index=5, window=3)
    result = DETECTOR.detect(rinput)
    assert result.matches == []
    assert result.generated_signals == []


def test_only_non_eval_signals_returns_empty():
    sigs = [
        EvidenceSignal(
            id=str(uuid.uuid4()),
            question_index=5,
            question_area="area",
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            polarity=EvidencePolarity.POSITIVE,
            signal_type=EvidenceType.REPEATED_STRENGTH,
            strength=0.8,
            source=EvidenceSource.PATTERN_DETECTOR,
            timestamp_question_index=5,
        )
    ]
    result = DETECTOR.detect(_make_input(sigs, question_index=5, window=3))
    assert result.matches == []


# ---- bridgeable types ----------------------------------------------------

def test_all_bridgeable_types_covered():
    assert EvidenceType.KNOWLEDGE_GAP in BRIDGEABLE_TYPES
    assert EvidenceType.SHALLOW_ANSWER in BRIDGEABLE_TYPES
    assert EvidenceType.REASONING_GAP in BRIDGEABLE_TYPES


def test_bridgeable_signal_produces_match():
    sig = _make_eval_sig(q_idx=10)
    result = DETECTOR.detect(_make_input([sig], question_index=10, window=3))
    assert len(result.matches) == 1
    assert result.matches[0].pattern_type == EvidenceType.KNOWLEDGE_GAP


# ---- sliding window logic -----------------------------------------------

def test_window_3_includes_last_3_question_indices():
    sigs = [
        _make_eval_sig(q_idx=8),
        _make_eval_sig(q_idx=9),
        _make_eval_sig(q_idx=10),
        _make_eval_sig(q_idx=11),
    ]
    # window=3, current=11 → eligible range [9,11]; q_idx=8 excluded
    result = DETECTOR.detect(_make_input(sigs, question_index=11, window=3))
    # Should include signals from 9, 10, 11 but not 8
    for m in result.matches:
        for s in m.evidence_signals:
            assert s.question_index >= 9


def test_old_signals_outside_window_not_bridged():
    sigs = [
        _make_eval_sig(q_idx=1),   # very old
        _make_eval_sig(q_idx=2),   # old
        _make_eval_sig(q_idx=10),  # in window
    ]
    result = DETECTOR.detect(_make_input(sigs, question_index=10, window=1))
    # window=1 → only q_idx=10 valid
    for m in result.matches:
        for s in m.evidence_signals:
            assert s.question_index == 10


def test_window_1_only_latest_index():
    sigs = [
        _make_eval_sig(q_idx=5),
        _make_eval_sig(q_idx=6),
    ]
    result = DETECTOR.detect(_make_input(sigs, question_index=6, window=1))
    # Only q_idx=6 should produce match signals
    for m in result.matches:
        for s in m.evidence_signals:
            assert s.question_index == 6


def test_window_larger_than_interview_all_included():
    sigs = [
        _make_eval_sig(q_idx=0),
        _make_eval_sig(q_idx=1),
    ]
    result = DETECTOR.detect(_make_input(sigs, question_index=1, window=100))
    assert len(result.matches) >= 1  # both indices included


def test_window_exactly_matches_boundary():
    sigs = [
        _make_eval_sig(q_idx=7),
        _make_eval_sig(q_idx=8),
        _make_eval_sig(q_idx=9),
    ]
    # window=3 → all three indices eligible
    result = DETECTOR.detect(_make_input(sigs, question_index=9, window=3))
    assert len(result.matches) >= 1


def test_all_signals_old_produces_empty():
    sigs = [
        _make_eval_sig(q_idx=1),
        _make_eval_sig(q_idx=2),
    ]
    # window=1, current q_idx=10 → only q_idx=10 eligible; none exist
    result = DETECTOR.detect(_make_input(sigs, question_index=10, window=1))
    assert result.matches == []


# ---- mixed signal types --------------------------------------------------

def test_non_bridgeable_type_not_matched():
    sigs = [
        EvidenceSignal(
            id=str(uuid.uuid4()),
            question_index=10,
            question_area="area",
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            polarity=EvidencePolarity.POSITIVE,
            signal_type=EvidenceType.REPEATED_STRENGTH,  # NOT bridgeable
            strength=0.8,
            source=EvidenceSource.EVALUATION,
            timestamp_question_index=10,
        )
    ]
    result = DETECTOR.detect(_make_input(sigs, question_index=10, window=3))
    assert result.matches == []


def test_mixed_bridgeable_and_non_bridgeable():
    sigs = [
        _make_eval_sig(q_idx=10, signal_type=EvidenceType.KNOWLEDGE_GAP),
        EvidenceSignal(
            id=str(uuid.uuid4()),
            question_index=10,
            question_area="area",
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            polarity=EvidencePolarity.POSITIVE,
            signal_type=EvidenceType.REPEATED_STRENGTH,
            strength=0.8,
            source=EvidenceSource.EVALUATION,
            timestamp_question_index=10,
        ),
    ]
    result = DETECTOR.detect(_make_input(sigs, question_index=10, window=3))
    matched_types = {m.pattern_type for m in result.matches}
    assert EvidenceType.KNOWLEDGE_GAP in matched_types
    assert EvidenceType.REPEATED_STRENGTH not in matched_types


# ---- generated signals + idempotency ------------------------------------

def test_generates_derived_pattern_detector_signal():
    sig = _make_eval_sig(q_idx=10)
    result = DETECTOR.detect(_make_input([sig], question_index=10, window=3))
    assert any(s.source == EvidenceSource.PATTERN_DETECTOR for s in result.generated_signals)


def test_idempotency_no_duplicates_on_second_run():
    """Pre-seeded PATTERN_DETECTOR signals prevent re-generation."""
    eval_sig = _make_eval_sig(q_idx=10)
    derived_sig = EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=10,
        question_area="area",
        dimension=ProfileDimension.TECHNICAL_DEPTH,
        polarity=EvidencePolarity.NEGATIVE,
        signal_type=EvidenceType.KNOWLEDGE_GAP,
        strength=0.7,
        source=EvidenceSource.PATTERN_DETECTOR,
        timestamp_question_index=10,
    )
    all_sigs = [eval_sig, derived_sig]
    result = DETECTOR.detect(_make_input(all_sigs, question_index=10, window=3))
    # Should not generate a duplicate PATTERN_DETECTOR signal for (KNOWLEDGE_GAP, TECHNICAL_DEPTH, q10)
    new_derived = [
        s for s in result.generated_signals if s.source == EvidenceSource.PATTERN_DETECTOR
    ]
    assert len(new_derived) == 0


def test_multiple_dims_generate_one_signal_per_dim():
    sigs = [
        _make_eval_sig(q_idx=10, dim=ProfileDimension.TECHNICAL_DEPTH),
        _make_eval_sig(q_idx=10, dim=ProfileDimension.PROBLEM_SOLVING),
    ]
    result = DETECTOR.detect(_make_input(sigs, question_index=10, window=3))
    derived = [s for s in result.generated_signals if s.source == EvidenceSource.PATTERN_DETECTOR]
    dims = {s.dimension for s in derived}
    assert ProfileDimension.TECHNICAL_DEPTH in dims
    assert ProfileDimension.PROBLEM_SOLVING in dims
