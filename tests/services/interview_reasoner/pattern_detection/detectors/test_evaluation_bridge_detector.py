# tests/services/interview_reasoner/pattern_detection/detectors/test_evaluation_bridge_detector.py
"""Tests for EvaluationBridgeDetector (M2-6A, P0 fix)."""

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
from services.interview_reasoner.pattern_detection.detectors.evaluation_bridge_detector import (
    EvaluationBridgeDetector,
    BRIDGEABLE_TYPES,
)


def _uid() -> str:
    return str(uuid.uuid4())


def _eval_sig(
    q: int = 1,
    dim: ProfileDimension = ProfileDimension.TECHNICAL_DEPTH,
    stype: EvidenceType = EvidenceType.KNOWLEDGE_GAP,
    polarity: EvidencePolarity = EvidencePolarity.NEGATIVE,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=_uid(), question_index=q, question_area="area",
        dimension=dim, polarity=polarity, signal_type=stype,
        strength=0.7, source=EvidenceSource.EVALUATION,
        timestamp_question_index=q,
    )


def _inp(signals: list[EvidenceSignal] | None = None, q_idx: int = 2) -> ReasonerInput:
    store = EvidenceStore(signals=signals or [])
    memory = InterviewMemory(evidence_store=store)
    return ReasonerInput(session_id="s", question_index=q_idx, interview_memory=memory, current_question_area="area")


# ---- metadata ----

def test_metadata_name():
    assert EvaluationBridgeDetector().metadata.name == "EvaluationBridgeDetector"


def test_metadata_priority_5():
    assert EvaluationBridgeDetector().metadata.priority == 5


def test_metadata_no_dependencies():
    assert EvaluationBridgeDetector().metadata.dependencies == []


def test_metadata_enabled():
    assert EvaluationBridgeDetector().metadata.enabled is True


# ---- empty store ----

def test_empty_store_no_output():
    result = EvaluationBridgeDetector().detect(_inp())
    assert result.generated_signals == []
    assert result.matches == []


# ---- KNOWLEDGE_GAP ----

def test_knowledge_gap_produces_match():
    sig = _eval_sig(stype=EvidenceType.KNOWLEDGE_GAP)
    result = EvaluationBridgeDetector().detect(_inp([sig]))
    assert any(m.pattern_type == EvidenceType.KNOWLEDGE_GAP for m in result.matches)


def test_knowledge_gap_produces_derived_signal():
    sig = _eval_sig(stype=EvidenceType.KNOWLEDGE_GAP)
    result = EvaluationBridgeDetector().detect(_inp([sig]))
    assert any(s.signal_type == EvidenceType.KNOWLEDGE_GAP for s in result.generated_signals)


def test_knowledge_gap_derived_source_is_pattern_detector():
    sig = _eval_sig(stype=EvidenceType.KNOWLEDGE_GAP)
    result = EvaluationBridgeDetector().detect(_inp([sig]))
    derived = [s for s in result.generated_signals if s.signal_type == EvidenceType.KNOWLEDGE_GAP]
    assert all(s.source == EvidenceSource.PATTERN_DETECTOR for s in derived)


# ---- SHALLOW_ANSWER ----

def test_shallow_answer_produces_match():
    sig = _eval_sig(stype=EvidenceType.SHALLOW_ANSWER)
    result = EvaluationBridgeDetector().detect(_inp([sig]))
    assert any(m.pattern_type == EvidenceType.SHALLOW_ANSWER for m in result.matches)


# ---- REASONING_GAP ----

def test_reasoning_gap_produces_match():
    sig = _eval_sig(stype=EvidenceType.REASONING_GAP)
    result = EvaluationBridgeDetector().detect(_inp([sig]))
    assert any(m.pattern_type == EvidenceType.REASONING_GAP for m in result.matches)


# ---- non-bridgeable signals are ignored ----

def test_non_bridgeable_type_ignored():
    sig = _eval_sig(stype=EvidenceType.REPEATED_STRENGTH, polarity=EvidencePolarity.POSITIVE)
    result = EvaluationBridgeDetector().detect(_inp([sig]))
    assert result.generated_signals == []
    assert result.matches == []


def test_pattern_detector_source_not_bridged():
    sig = EvidenceSignal(
        id=_uid(), question_index=1, question_area="a",
        dimension=ProfileDimension.TECHNICAL_DEPTH,
        polarity=EvidencePolarity.NEGATIVE,
        signal_type=EvidenceType.KNOWLEDGE_GAP,
        strength=0.7,
        source=EvidenceSource.PATTERN_DETECTOR,
        timestamp_question_index=1,
    )
    result = EvaluationBridgeDetector().detect(_inp([sig]))
    assert result.generated_signals == []


# ---- mixed signals ----

def test_mixed_signals_only_bridgeable_matched():
    bridgeable = _eval_sig(stype=EvidenceType.KNOWLEDGE_GAP)
    non_bridgeable = _eval_sig(stype=EvidenceType.REPEATED_STRENGTH, polarity=EvidencePolarity.POSITIVE)
    result = EvaluationBridgeDetector().detect(_inp([bridgeable, non_bridgeable]))
    assert len(result.matches) == 1
    assert result.matches[0].pattern_type == EvidenceType.KNOWLEDGE_GAP


# ---- idempotency / duplicate prevention ----

def test_no_duplicate_derived_signal_on_second_run():
    sig = _eval_sig(stype=EvidenceType.KNOWLEDGE_GAP)
    # First run: store has only evaluation sig
    inp1 = _inp([sig])
    r1 = EvaluationBridgeDetector().detect(inp1)
    assert len(r1.generated_signals) == 1

    # Second run: store now contains the derived PATTERN_DETECTOR signal too
    derived = r1.generated_signals[0]
    store2 = EvidenceStore(signals=[sig, derived])
    memory2 = InterviewMemory(evidence_store=store2)
    inp2 = ReasonerInput(session_id="s", question_index=2, interview_memory=memory2, current_question_area="area")
    r2 = EvaluationBridgeDetector().detect(inp2)
    # Derived signal already present → idempotency filter removes it
    assert len(r2.generated_signals) == 0


def test_one_derived_per_dimension_not_per_signal():
    # Two KNOWLEDGE_GAP signals on same dim → only one derived signal
    s1 = _eval_sig(q=1, stype=EvidenceType.KNOWLEDGE_GAP)
    s2 = _eval_sig(q=2, stype=EvidenceType.KNOWLEDGE_GAP)  # same dim
    result = EvaluationBridgeDetector().detect(_inp([s1, s2]))
    derived = [s for s in result.generated_signals if s.signal_type == EvidenceType.KNOWLEDGE_GAP]
    assert len(derived) == 1


# ---- BRIDGEABLE_TYPES constant ----

def test_bridgeable_types_contains_expected():
    assert EvidenceType.KNOWLEDGE_GAP in BRIDGEABLE_TYPES
    assert EvidenceType.SHALLOW_ANSWER in BRIDGEABLE_TYPES
    assert EvidenceType.REASONING_GAP in BRIDGEABLE_TYPES


def test_result_detector_name():
    assert EvaluationBridgeDetector().detect(_inp()).detector_name == "EvaluationBridgeDetector"
