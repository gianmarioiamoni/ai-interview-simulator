# tests/services/interview_reasoner/pattern_detection/detectors/test_communication_detector.py
"""Tests for CommunicationDetector (M2-7C, DET-07).

Coverage:
  - Clear structure → COMMUNICATION_CLEAR
  - Poor structure → COMMUNICATION_WEAK (PatternMatch: COMMUNICATION_GAP)
  - Verbosity/conciseness
  - Logical progression → CLEAR
  - Inconsistent signals → CONTRADICTORY_ANSWER match
  - Silent when insufficient evidence (< 2 signals)
  - Idempotency
  - Metadata: priority=60, depends=ConsistencyDetector
  - False positives: wrong dimension ignored
  - Does not evaluate grammar / knowledge
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
from services.interview_reasoner.pattern_detection.detectors.communication_detector import (
    CommunicationDetector,
)

DETECTOR = CommunicationDetector()
_DIM = ProfileDimension.COMMUNICATION


def _sig(
    signal_type: EvidenceType,
    polarity: EvidencePolarity,
    q_idx: int = 3,
    dim: ProfileDimension = _DIM,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=q_idx,
        question_area="api_design",
        dimension=dim,
        polarity=polarity,
        signal_type=signal_type,
        strength=0.7,
        source=EvidenceSource.EVALUATION,
        timestamp_question_index=q_idx,
    )


def _make_input(signals: list[EvidenceSignal], q_idx: int = 5) -> ReasonerInput:
    store = EvidenceStore()
    for s in signals:
        store = store.append(s)
    metrics = SessionMetrics(questions_answered=q_idx)
    memory = InterviewMemory(evidence_store=store, session_metrics=metrics)
    return ReasonerInput(
        session_id="test",
        question_index=q_idx,
        interview_memory=memory,
        current_question_area="api_design",
    )


# ---- metadata ---------------------------------------------------------------

def test_metadata_name():
    assert DETECTOR.metadata.name == "CommunicationDetector"


def test_metadata_priority():
    assert DETECTOR.metadata.priority == 60


def test_metadata_depends_on_consistency():
    assert "ConsistencyDetector" in DETECTOR.metadata.dependencies


def test_metadata_version():
    assert DETECTOR.metadata.version == "1.0.0"


# ---- clear structure -------------------------------------------------------

def test_clear_structure_emits_communication_clear():
    sigs = [
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.COMMUNICATION_CLEAR in types


def test_logical_progression_gives_clear():
    sigs = [
        _sig(EvidenceType.DEMONSTRATED_DEPTH, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.DEMONSTRATED_DEPTH, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.NEGATIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.COMMUNICATION_CLEAR in types


# ---- poor structure / verbosity --------------------------------------------

def test_poor_structure_emits_communication_gap_match():
    sigs = [
        _sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.SHALLOW_ANSWER, EvidencePolarity.NEGATIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.COMMUNICATION_GAP in types


def test_verbosity_pattern_gives_weak():
    # Simulates: 5 COMMUNICATION_GAP + 1 REPEATED_STRENGTH
    sigs = [
        _sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.COMMUNICATION_GAP in types


# ---- inconsistency ---------------------------------------------------------

def test_inconsistent_signals_emit_contradictory_match():
    sigs = [
        _sig(EvidenceType.CONTRADICTORY_ANSWER, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.CONTRADICTORY_ANSWER in types


# ---- silence guard (< 2 evidence) -----------------------------------------

def test_silent_with_no_evidence():
    result = DETECTOR.detect(_make_input([]))
    assert result.matches == []
    assert result.generated_signals == []


def test_silent_with_single_signal():
    sigs = [_sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.NEGATIVE)]
    result = DETECTOR.detect(_make_input(sigs))
    assert result.matches == []
    assert result.generated_signals == []


# ---- false positives --------------------------------------------------------

def test_wrong_dimension_signals_ignored():
    sigs = [
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE, dim=ProfileDimension.TECHNICAL_DEPTH),
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE, dim=ProfileDimension.TECHNICAL_DEPTH),
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE, dim=ProfileDimension.ENGINEERING_JUDGMENT),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.COMMUNICATION_CLEAR not in types


def test_knowledge_gap_on_other_dim_not_counted():
    sigs = [
        _sig(EvidenceType.KNOWLEDGE_GAP, EvidencePolarity.NEGATIVE, dim=ProfileDimension.TECHNICAL_DEPTH),
        _sig(EvidenceType.KNOWLEDGE_GAP, EvidencePolarity.NEGATIVE, dim=ProfileDimension.TECHNICAL_DEPTH),
        _sig(EvidenceType.KNOWLEDGE_GAP, EvidencePolarity.NEGATIVE, dim=ProfileDimension.TECHNICAL_DEPTH),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert result.matches == []


# ---- idempotency -----------------------------------------------------------

def test_idempotency_does_not_re_emit():
    sigs = [
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
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


# ---- signal contracts ------------------------------------------------------

def test_generated_signal_source_is_pattern_detector():
    sigs = [
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    for sig in result.generated_signals:
        assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_generated_signal_dimension_is_communication():
    sigs = [
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    for sig in result.generated_signals:
        assert sig.dimension == ProfileDimension.COMMUNICATION


def test_label_includes_verdict():
    sigs = [
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.REPEATED_STRENGTH, EvidencePolarity.POSITIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert any("communication" in m.label for m in result.matches)
