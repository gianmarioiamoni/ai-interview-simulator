# tests/services/interview_reasoner/pattern_detection/detectors/test_reasoning_depth_detector.py
"""Tests for ReasoningDepthDetector (M2-7B).

Coverage:
  - Repeated shallow reasoning → REASONING_DEPTH_LOW
  - Deep reasoning → REASONING_DEPTH_HIGH
  - Improving trend → REASONING_IMPROVING
  - Stagnating trend → REASONING_STAGNATING
  - Stable reasoning (neutral, no signal)
  - Regression scenario
  - Contradictory evidence (mixed)
  - Increasing evidence quality
  - No evidence → empty result
  - Idempotency
  - Metadata: priority=40, depends=TrendDetector
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
from domain.contracts.reasoning.reasoning_history import ReasoningEntry, ReasoningHistory
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.reasoning.session_metrics import SessionMetrics
from services.interview_reasoner.pattern_detection.detectors.reasoning_depth_detector import (
    ReasoningDepthDetector,
)

DETECTOR = ReasoningDepthDetector()

_DIM = ProfileDimension.TECHNICAL_DEPTH


def _sig(
    signal_type: EvidenceType,
    polarity: EvidencePolarity,
    q_idx: int = 5,
    dim: ProfileDimension = _DIM,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=q_idx,
        question_area="area",
        dimension=dim,
        polarity=polarity,
        signal_type=signal_type,
        strength=0.7,
        source=EvidenceSource.EVALUATION,
        timestamp_question_index=q_idx,
    )


def _make_input(
    signals: list[EvidenceSignal],
    history_entries: list[ReasoningEntry] | None = None,
    question_index: int = 5,
) -> ReasonerInput:
    store = EvidenceStore(signals=signals)
    history = ReasoningHistory(entries=history_entries or [])
    memory = InterviewMemory(
        evidence_store=store,
        reasoning_history=history,
        session_metrics=SessionMetrics(questions_answered=question_index),
    )
    return ReasonerInput(
        session_id="test",
        question_index=question_index,
        interview_memory=memory,
        current_question_area="area",
    )


def _deep_sigs(n: int = 4, q_idx: int = 5) -> list[EvidenceSignal]:
    return [_sig(EvidenceType.DEMONSTRATED_DEPTH, EvidencePolarity.POSITIVE, q_idx=q_idx) for _ in range(n)]


def _shallow_sigs(n: int = 4, q_idx: int = 5) -> list[EvidenceSignal]:
    return [_sig(EvidenceType.SHALLOW_ANSWER, EvidencePolarity.NEGATIVE, q_idx=q_idx) for _ in range(n)]


# ---- metadata -----------------------------------------------------------

def test_metadata_priority_is_40():
    assert DETECTOR.metadata.priority == 40


def test_metadata_depends_on_trend_detector():
    assert "TrendDetector" in DETECTOR.metadata.dependencies


def test_metadata_name():
    assert DETECTOR.metadata.name == "ReasoningDepthDetector"


# ---- no evidence --------------------------------------------------------

def test_no_signals_returns_empty():
    result = DETECTOR.detect(_make_input([]))
    assert result.matches == []
    assert result.generated_signals == []


def test_no_relevant_signals_returns_empty():
    sigs = [_sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.NEGATIVE)]
    result = DETECTOR.detect(_make_input(sigs))
    assert result.matches == []


# ---- depth verdicts -----------------------------------------------------

def test_repeated_shallow_reasoning_emits_depth_low():
    sigs = _shallow_sigs(5)  # all shallow, > MIN_EVIDENCE
    result = DETECTOR.detect(_make_input(sigs))
    types = {m.pattern_type for m in result.matches}
    assert EvidenceType.REASONING_DEPTH_LOW in types


def test_deep_reasoning_emits_depth_high():
    sigs = _deep_sigs(5)  # all deep, > MIN_EVIDENCE
    result = DETECTOR.detect(_make_input(sigs))
    types = {m.pattern_type for m in result.matches}
    assert EvidenceType.REASONING_DEPTH_HIGH in types


def test_stable_mixed_evidence_no_depth_signal():
    # Equal deep/shallow → neutral → no DEPTH_HIGH or DEPTH_LOW
    sigs = _deep_sigs(2) + _shallow_sigs(2)  # total=4 but ratio=0.5
    result = DETECTOR.detect(_make_input(sigs))
    types = {m.pattern_type for m in result.matches}
    assert EvidenceType.REASONING_DEPTH_HIGH not in types
    assert EvidenceType.REASONING_DEPTH_LOW not in types


def test_insufficient_evidence_no_verdict():
    sigs = _shallow_sigs(2)  # total=2 < MIN_EVIDENCE=3
    result = DETECTOR.detect(_make_input(sigs))
    types = {m.pattern_type for m in result.matches}
    assert EvidenceType.REASONING_DEPTH_LOW not in types


# ---- trend signals -------------------------------------------------------

def _entry_with_patterns(q_idx: int, patterns: list[EvidenceType]) -> ReasoningEntry:
    return ReasoningEntry(
        question_index=q_idx,
        detected_patterns=patterns,
    )


def test_improving_trend_emits_reasoning_improving():
    # Ratios from detected_patterns must be strictly increasing for last TREND_WINDOW entries.
    # Entry 0: 0 deep, 1 shallow → ratio=0.0
    # Entry 1: 1 deep, 0 shallow → ratio=1.0
    # But we need strict increasing: [0.0, 0.5, 1.0] → 3 entries strict increasing
    entries = [
        _entry_with_patterns(0, [EvidenceType.REASONING_DEPTH_LOW]),           # ratio=0.0
        _entry_with_patterns(1, [EvidenceType.REASONING_DEPTH_HIGH,
                                  EvidenceType.REASONING_DEPTH_LOW]),           # ratio=0.5
        _entry_with_patterns(2, [EvidenceType.REASONING_DEPTH_HIGH]),          # ratio=1.0
    ]
    sigs = _deep_sigs(4)
    result = DETECTOR.detect(_make_input(sigs, history_entries=entries))
    types = {m.pattern_type for m in result.matches}
    assert EvidenceType.REASONING_IMPROVING in types


def test_stagnating_trend_emits_reasoning_stagnating():
    entries = [
        _entry_with_patterns(0, [EvidenceType.REASONING_DEPTH_LOW]),
        _entry_with_patterns(1, [EvidenceType.REASONING_DEPTH_LOW]),
        _entry_with_patterns(2, [EvidenceType.REASONING_DEPTH_LOW]),
    ]
    sigs = _shallow_sigs(5)
    result = DETECTOR.detect(_make_input(sigs, history_entries=entries))
    types = {m.pattern_type for m in result.matches}
    assert EvidenceType.REASONING_STAGNATING in types


def test_insufficient_history_no_trend():
    entries = [
        _entry_with_patterns(0, [EvidenceType.REASONING_DEPTH_HIGH]),
    ]
    sigs = _deep_sigs(4)
    result = DETECTOR.detect(_make_input(sigs, history_entries=entries))
    types = {m.pattern_type for m in result.matches}
    assert EvidenceType.REASONING_IMPROVING not in types
    assert EvidenceType.REASONING_STAGNATING not in types


def test_regression_after_high_now_low():
    # Was deep → now mostly shallow
    entries = [
        _entry_with_patterns(0, [EvidenceType.REASONING_DEPTH_HIGH]),
        _entry_with_patterns(1, [EvidenceType.REASONING_DEPTH_HIGH]),
        _entry_with_patterns(2, [EvidenceType.REASONING_DEPTH_LOW]),
    ]
    sigs = _shallow_sigs(5)  # current cycle is shallow
    result = DETECTOR.detect(_make_input(sigs, history_entries=entries))
    types = {m.pattern_type for m in result.matches}
    assert EvidenceType.REASONING_DEPTH_LOW in types


# ---- contradictory evidence ---------------------------------------------

def test_contradictory_evidence_produces_neutral_or_low():
    # Some deep, some shallow — balance determines verdict
    sigs = _deep_sigs(2) + _shallow_sigs(4)  # shallow wins
    result = DETECTOR.detect(_make_input(sigs))
    types = {m.pattern_type for m in result.matches}
    # Should not emit HIGH since shallow outweighs deep
    assert EvidenceType.REASONING_DEPTH_HIGH not in types


def test_increasing_quality_multi_dim():
    sigs = (
        _deep_sigs(4, q_idx=5)
        + [_sig(EvidenceType.DEMONSTRATED_DEPTH, EvidencePolarity.POSITIVE, q_idx=5,
                dim=ProfileDimension.PROBLEM_SOLVING)] * 4
    )
    result = DETECTOR.detect(_make_input(sigs))
    types = {m.pattern_type for m in result.matches}
    assert EvidenceType.REASONING_DEPTH_HIGH in types


# ---- idempotency --------------------------------------------------------

def test_idempotency_no_duplicate_signals():
    sigs = _shallow_sigs(5)
    result1 = DETECTOR.detect(_make_input(sigs))
    # Inject generated signals back into store
    all_sigs = sigs + result1.generated_signals
    result2 = DETECTOR.detect(_make_input(all_sigs))
    # No new signals should be generated that duplicate existing ones
    existing_keys = {
        (s.signal_type, s.dimension, s.source) for s in result1.generated_signals
    }
    for s in result2.generated_signals:
        key = (s.signal_type, s.dimension, s.source)
        assert key not in existing_keys, f"Duplicate signal found: {key}"


# ---- generated signals source -------------------------------------------

def test_generated_signals_have_pattern_detector_source():
    sigs = _deep_sigs(5)
    result = DETECTOR.detect(_make_input(sigs))
    for s in result.generated_signals:
        assert s.source == EvidenceSource.PATTERN_DETECTOR
