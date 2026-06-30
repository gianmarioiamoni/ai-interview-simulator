# tests/services/interview_reasoner/pattern_detection/detectors/test_consistency_detector.py

import pytest
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoning_history import ReasoningEntry, ReasoningHistory
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.detectors.consistency_detector import ConsistencyDetector

from tests.services.interview_reasoner.pattern_detection.detectors.conftest import (
    make_input,
    make_signal,
    make_reasoning_entry,
)

# ---- metadata ----

def test_metadata_name():
    assert ConsistencyDetector().metadata.name == "ConsistencyDetector"


def test_metadata_priority():
    assert ConsistencyDetector().metadata.priority == 20


def test_metadata_depends_on_coverage():
    assert "CoverageDetector" in ConsistencyDetector().metadata.dependencies


def test_metadata_enabled():
    assert ConsistencyDetector().metadata.enabled is True


# ---- empty memory → no signals ----

def test_empty_memory_no_output():
    result = ConsistencyDetector().detect(make_input())
    assert result.evidence == []


# ---- duplicate detection ----

def test_duplicate_signals_flagged():
    s1 = make_signal(q_idx=1, dim=ProfileDimension.TECHNICAL_DEPTH,
                     polarity=EvidencePolarity.NEGATIVE,
                     signal_type=EvidenceType.SHALLOW_ANSWER)
    s2 = make_signal(q_idx=1, dim=ProfileDimension.TECHNICAL_DEPTH,
                     polarity=EvidencePolarity.NEGATIVE,
                     signal_type=EvidenceType.SHALLOW_ANSWER)
    store = EvidenceStore(signals=[s1, s2])
    memory = InterviewMemory(evidence_store=store)
    inp = make_input(memory=memory)
    result = ConsistencyDetector().detect(inp)
    dups = [e for e in result.evidence if e.signal_type == EvidenceType.REPEATED_WEAKNESS]
    assert len(dups) == 1


def test_no_duplicate_when_different_questions():
    s1 = make_signal(q_idx=1, dim=ProfileDimension.TECHNICAL_DEPTH)
    s2 = make_signal(q_idx=2, dim=ProfileDimension.TECHNICAL_DEPTH)
    store = EvidenceStore(signals=[s1, s2])
    memory = InterviewMemory(evidence_store=store)
    result = ConsistencyDetector().detect(make_input(memory=memory))
    dups = [e for e in result.evidence if e.signal_type == EvidenceType.REPEATED_WEAKNESS]
    assert dups == []


def test_no_duplicate_different_polarity_same_question():
    # Different polarity → not a duplicate key; will be caught by contradiction check
    s1 = make_signal(q_idx=1, polarity=EvidencePolarity.NEGATIVE)
    s2 = make_signal(q_idx=1, polarity=EvidencePolarity.POSITIVE,
                     signal_type=EvidenceType.REPEATED_STRENGTH)
    store = EvidenceStore(signals=[s1, s2])
    memory = InterviewMemory(evidence_store=store)
    result = ConsistencyDetector().detect(make_input(memory=memory))
    dups = [e for e in result.evidence if e.signal_type == EvidenceType.REPEATED_WEAKNESS]
    assert dups == []


# ---- contradiction detection ----

def test_contradictory_signals_flagged():
    pos = make_signal(q_idx=1, polarity=EvidencePolarity.POSITIVE,
                      signal_type=EvidenceType.REPEATED_STRENGTH)
    neg = make_signal(q_idx=1, polarity=EvidencePolarity.NEGATIVE)
    store = EvidenceStore(signals=[pos, neg])
    memory = InterviewMemory(evidence_store=store)
    result = ConsistencyDetector().detect(make_input(memory=memory))
    contradictions = [e for e in result.evidence if e.signal_type == EvidenceType.CONTRADICTORY_ANSWER]
    assert len(contradictions) == 1


def test_no_contradiction_when_same_polarity():
    s1 = make_signal(q_idx=1, polarity=EvidencePolarity.NEGATIVE)
    s2 = make_signal(q_idx=1, polarity=EvidencePolarity.NEGATIVE,
                     signal_type=EvidenceType.KNOWLEDGE_GAP)
    store = EvidenceStore(signals=[s1, s2])
    memory = InterviewMemory(evidence_store=store)
    result = ConsistencyDetector().detect(make_input(memory=memory))
    contradictions = [e for e in result.evidence if e.signal_type == EvidenceType.CONTRADICTORY_ANSWER]
    assert contradictions == []


def test_contradiction_on_correct_dimension():
    pos = make_signal(q_idx=2, dim=ProfileDimension.COMMUNICATION,
                      polarity=EvidencePolarity.POSITIVE,
                      signal_type=EvidenceType.REPEATED_STRENGTH)
    neg = make_signal(q_idx=2, dim=ProfileDimension.COMMUNICATION,
                      polarity=EvidencePolarity.NEGATIVE)
    store = EvidenceStore(signals=[pos, neg])
    memory = InterviewMemory(evidence_store=store)
    result = ConsistencyDetector().detect(make_input(memory=memory))
    cont = [e for e in result.evidence if e.signal_type == EvidenceType.CONTRADICTORY_ANSWER]
    assert len(cont) == 1
    assert cont[0].dimension == ProfileDimension.COMMUNICATION


# ---- confidence drop detection ----

def test_confidence_drop_detected():
    e1 = make_reasoning_entry(q_idx=0, reasoning_confidence=0.9)
    e2 = make_reasoning_entry(q_idx=1, reasoning_confidence=0.9)
    e3 = make_reasoning_entry(q_idx=2, reasoning_confidence=0.5)  # big drop
    history = ReasoningHistory(entries=[e1, e2, e3])
    memory = InterviewMemory(reasoning_history=history)
    result = ConsistencyDetector().detect(make_input(memory=memory))
    drops = [e for e in result.evidence if e.signal_type == EvidenceType.CONFIDENCE_DROP]
    assert len(drops) == 1


def test_no_confidence_drop_when_stable():
    e1 = make_reasoning_entry(q_idx=0, reasoning_confidence=0.7)
    e2 = make_reasoning_entry(q_idx=1, reasoning_confidence=0.7)
    history = ReasoningHistory(entries=[e1, e2])
    memory = InterviewMemory(reasoning_history=history)
    result = ConsistencyDetector().detect(make_input(memory=memory))
    drops = [e for e in result.evidence if e.signal_type == EvidenceType.CONFIDENCE_DROP]
    assert drops == []


def test_single_entry_no_confidence_drop():
    history = ReasoningHistory(entries=[make_reasoning_entry()])
    memory = InterviewMemory(reasoning_history=history)
    result = ConsistencyDetector().detect(make_input(memory=memory))
    drops = [e for e in result.evidence if e.signal_type == EvidenceType.CONFIDENCE_DROP]
    assert drops == []


def test_confidence_drop_skips_dim_without_enough_entries():
    # Only one entry per dimension → no drop
    e1 = make_reasoning_entry(q_idx=0, dominant_dimension=ProfileDimension.TECHNICAL_DEPTH, reasoning_confidence=0.9)
    e2 = make_reasoning_entry(q_idx=1, dominant_dimension=ProfileDimension.COMMUNICATION, reasoning_confidence=0.5)
    history = ReasoningHistory(entries=[e1, e2])
    memory = InterviewMemory(reasoning_history=history)
    result = ConsistencyDetector().detect(make_input(memory=memory))
    drops = [e for e in result.evidence if e.signal_type == EvidenceType.CONFIDENCE_DROP]
    assert drops == []


def test_confidence_drop_strength_capped_at_1():
    # drop = 0.9 - 0.1 = 0.8 → base 0.6 + 0.8 = 1.4, should be capped at 1.0
    e1 = make_reasoning_entry(q_idx=0, reasoning_confidence=0.9)
    e2 = make_reasoning_entry(q_idx=1, reasoning_confidence=0.9)
    e3 = make_reasoning_entry(q_idx=2, reasoning_confidence=0.1)
    history = ReasoningHistory(entries=[e1, e2, e3])
    memory = InterviewMemory(reasoning_history=history)
    result = ConsistencyDetector().detect(make_input(memory=memory))
    drops = [e for e in result.evidence if e.signal_type == EvidenceType.CONFIDENCE_DROP]
    assert all(e.strength <= 1.0 for e in drops)


def test_result_detector_name():
    result = ConsistencyDetector().detect(make_input())
    assert result.detector_name == "ConsistencyDetector"


def test_none_area_defaults_to_unknown():
    inp = ReasonerInput(session_id="s", question_index=0)
    result = ConsistencyDetector().detect(inp)
    assert result.evidence == []
