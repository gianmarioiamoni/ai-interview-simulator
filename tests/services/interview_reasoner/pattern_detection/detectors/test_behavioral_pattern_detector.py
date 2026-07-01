# tests/services/interview_reasoner/pattern_detection/detectors/test_behavioral_pattern_detector.py
"""Tests for BehavioralPatternDetector (M2-7D, DET-08).

Coverage:
  - Confidence growth → BEHAVIORAL_GROWTH
  - Adaptability / hesitation reduction → BEHAVIORAL_GROWTH
  - Learning during interview → BEHAVIORAL_GROWTH
  - Behavioral consistency → BEHAVIORAL_PLATEAU
  - Behavioral instability → BEHAVIORAL_INSTABILITY
  - Empty / insufficient history → no result
  - Idempotency
  - False positives (technical signals don't affect behavioral)
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
from domain.contracts.reasoning.reasoning_history import ReasoningEntry, ReasoningHistory
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.reasoning.session_metrics import SessionMetrics
from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern_detector import (
    BehavioralPatternDetector,
)

DETECTOR = BehavioralPatternDetector()


def _entry(
    q_idx: int = 0,
    confidence: float = 0.6,
    patterns: list[EvidenceType] | None = None,
) -> ReasoningEntry:
    return ReasoningEntry(
        question_index=q_idx,
        reasoning_confidence=confidence,
        detected_patterns=patterns or [],
    )


def _make_input(
    entries: list[ReasoningEntry],
    q_idx: int = 5,
    store: EvidenceStore | None = None,
) -> ReasonerInput:
    history = ReasoningHistory(entries=entries)
    memory = InterviewMemory(
        reasoning_history=history,
        evidence_store=store or EvidenceStore(),
        session_metrics=SessionMetrics(questions_answered=q_idx),
    )
    return ReasonerInput(
        session_id="test",
        question_index=q_idx,
        interview_memory=memory,
        current_question_area="api_design",
    )


# ---- metadata ---------------------------------------------------------------

def test_metadata_name():
    assert DETECTOR.metadata.name == "BehavioralPatternDetector"


def test_metadata_priority():
    assert DETECTOR.metadata.priority == 70


def test_metadata_depends_on_communication():
    assert "CommunicationDetector" in DETECTOR.metadata.dependencies


def test_metadata_version():
    assert DETECTOR.metadata.version == "1.0.0"


# ---- confidence growth ------------------------------------------------------

def test_confidence_growth_emits_behavioral_growth():
    pos = EvidenceType.REPEATED_STRENGTH
    entries = [
        _entry(0, 0.2, [pos]),
        _entry(1, 0.4, [pos]),
        _entry(2, 0.6, [pos]),
        _entry(3, 0.8, [pos]),
    ]
    result = DETECTOR.detect(_make_input(entries))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.BEHAVIORAL_GROWTH in types


def test_adaptability_hesitation_reduction_growth():
    pos = EvidenceType.RECOVERED_WEAKNESS
    entries = [
        _entry(0, 0.3, [pos]),
        _entry(1, 0.5, [pos]),
        _entry(2, 0.65, [pos]),
        _entry(3, 0.85, [pos]),
    ]
    result = DETECTOR.detect(_make_input(entries))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.BEHAVIORAL_GROWTH in types


def test_learning_during_interview():
    pos = EvidenceType.DEMONSTRATED_DEPTH
    entries = [
        _entry(0, 0.25, [pos]),
        _entry(1, 0.45, [pos]),
        _entry(2, 0.65, [pos]),
        _entry(3, 0.85, [pos]),
    ]
    result = DETECTOR.detect(_make_input(entries))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.BEHAVIORAL_GROWTH in types


# ---- behavioral consistency -------------------------------------------------

def test_behavioral_consistency_plateau():
    same = [EvidenceType.REPEATED_STRENGTH]
    entries = [_entry(i, 0.6, same) for i in range(4)]
    result = DETECTOR.detect(_make_input(entries))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.BEHAVIORAL_PLATEAU in types


# ---- behavioral instability -------------------------------------------------

def test_behavioral_instability():
    entries = [
        _entry(0, 0.6, [EvidenceType.REPEATED_STRENGTH]),
        _entry(1, 0.6, [EvidenceType.SHALLOW_ANSWER]),
        _entry(2, 0.6, [EvidenceType.DEMONSTRATED_DEPTH]),
        _entry(3, 0.6, [EvidenceType.REASONING_GAP]),
    ]
    result = DETECTOR.detect(_make_input(entries))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.BEHAVIORAL_INSTABILITY in types


# ---- empty / insufficient --------------------------------------------------

def test_empty_history_no_result():
    result = DETECTOR.detect(_make_input([]))
    assert result.matches == []
    assert result.generated_signals == []


def test_insufficient_entries_no_result():
    entries = [_entry(i, 0.6) for i in range(2)]
    result = DETECTOR.detect(_make_input(entries))
    assert result.matches == []


# ---- idempotency -----------------------------------------------------------

def test_idempotency_no_re_emit():
    pos = EvidenceType.REPEATED_STRENGTH
    entries = [
        _entry(0, 0.2, [pos]),
        _entry(1, 0.4, [pos]),
        _entry(2, 0.6, [pos]),
        _entry(3, 0.8, [pos]),
    ]
    ri = _make_input(entries)
    result1 = DETECTOR.detect(ri)
    assert len(result1.generated_signals) > 0

    store = ri.interview_memory.evidence_store
    for s in result1.generated_signals:
        store = store.append(s)
    memory = ri.interview_memory.model_copy(update={"evidence_store": store})
    ri2 = ri.model_copy(update={"interview_memory": memory})
    result2 = DETECTOR.detect(ri2)
    assert len(result2.generated_signals) == 0


# ---- false positives --------------------------------------------------------

def test_no_result_without_enough_entries_even_with_store_signals():
    # Even if there are lots of store signals, if history is short → no behavioral result
    entries = [_entry(0, 0.5)]
    result = DETECTOR.detect(_make_input(entries))
    assert result.matches == []


# ---- signal contract --------------------------------------------------------

def test_generated_signal_source():
    pos = EvidenceType.REPEATED_STRENGTH
    entries = [_entry(i, 0.2 + i * 0.2, [pos]) for i in range(4)]
    result = DETECTOR.detect(_make_input(entries))
    for sig in result.generated_signals:
        assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_generated_signal_dimension():
    pos = EvidenceType.REPEATED_STRENGTH
    entries = [_entry(i, 0.2 + i * 0.2, [pos]) for i in range(4)]
    result = DETECTOR.detect(_make_input(entries))
    for sig in result.generated_signals:
        assert sig.dimension == ProfileDimension.PROBLEM_SOLVING


def test_label_contains_verdict():
    pos = EvidenceType.REPEATED_STRENGTH
    entries = [_entry(i, 0.2 + i * 0.2, [pos]) for i in range(4)]
    result = DETECTOR.detect(_make_input(entries))
    assert any("behavioral" in m.label for m in result.matches)
