# tests/services/interview_reasoner/pattern_detection/detectors/test_engineering_judgment_detector.py
"""Tests for EngineeringJudgmentDetector (M2-7C, DET-06).

Coverage:
  - Strong trade-off reasoning → ENGINEERING_JUDGMENT_HIGH
  - Poor operational thinking → ENGINEERING_JUDGMENT_LOW
  - No evaluation evidence → KNOWLEDGE_GAP
  - Mixed signals → NEUTRAL
  - Empty evidence → no result
  - Idempotency (filter_new_signals)
  - Metadata: priority=50, depends=ReasoningDepthDetector
  - Risk awareness signals
  - Maintainability signals
  - False positive prevention (wrong dimension ignored)
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
from services.interview_reasoner.pattern_detection.detectors.engineering_judgment_detector import (
    EngineeringJudgmentDetector,
)

DETECTOR = EngineeringJudgmentDetector()
_DIM = ProfileDimension.ENGINEERING_JUDGMENT


def _sig(
    signal_type: EvidenceType,
    polarity: EvidencePolarity,
    q_idx: int = 3,
    dim: ProfileDimension = _DIM,
    source: EvidenceSource = EvidenceSource.EVALUATION,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=q_idx,
        question_area="system_design",
        dimension=dim,
        polarity=polarity,
        signal_type=signal_type,
        strength=0.7,
        source=source,
        timestamp_question_index=q_idx,
    )


def _make_input(signals: list[EvidenceSignal], q_idx: int = 5, questions_answered: int = 5) -> ReasonerInput:
    store = EvidenceStore()
    for s in signals:
        store = store.append(s)
    metrics = SessionMetrics(questions_answered=questions_answered)
    memory = InterviewMemory(evidence_store=store, session_metrics=metrics)
    return ReasonerInput(
        session_id="test",
        question_index=q_idx,
        interview_memory=memory,
        current_question_area="system_design",
    )


# ---- metadata ---------------------------------------------------------------

def test_metadata_name():
    assert DETECTOR.metadata.name == "EngineeringJudgmentDetector"


def test_metadata_priority():
    assert DETECTOR.metadata.priority == 50


def test_metadata_depends_on_reasoning_depth():
    assert "ReasoningDepthDetector" in DETECTOR.metadata.dependencies


def test_metadata_version():
    assert DETECTOR.metadata.version == "1.0.0"


# ---- trade-off reasoning (HIGH) --------------------------------------------

def test_strong_trade_off_reasoning_emits_high():
    sigs = [
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.SHALLOW_ANSWER, EvidencePolarity.NEGATIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.ENGINEERING_JUDGMENT_HIGH in types


def test_demonstrated_depth_on_judgment_dim_positive():
    sigs = [
        _sig(EvidenceType.DEMONSTRATED_DEPTH, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.DEMONSTRATED_DEPTH, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.DEMONSTRATED_DEPTH, EvidencePolarity.POSITIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.ENGINEERING_JUDGMENT_HIGH in types


# ---- poor operational thinking (LOW) --------------------------------------

def test_poor_operational_thinking_emits_low():
    sigs = [
        _sig(EvidenceType.SHALLOW_ANSWER, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.SHALLOW_ANSWER, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.REASONING_GAP, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.ENGINEERING_JUDGMENT_LOW in types


def test_risk_awareness_absent_gives_low():
    sigs = [
        _sig(EvidenceType.KNOWLEDGE_GAP, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.KNOWLEDGE_GAP, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.REASONING_GAP, EvidencePolarity.NEGATIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.ENGINEERING_JUDGMENT_LOW in types


# ---- knowledge gap (no evaluation evidence) --------------------------------

def test_no_eval_evidence_emits_knowledge_gap():
    result = DETECTOR.detect(_make_input([]))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.KNOWLEDGE_GAP in types


def test_no_gap_emitted_when_not_enough_questions():
    result = DETECTOR.detect(_make_input([], questions_answered=1))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.KNOWLEDGE_GAP not in types


def test_gap_not_emitted_when_eval_evidence_exists():
    sigs = [
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.KNOWLEDGE_GAP not in types


# ---- false positives --------------------------------------------------------

def test_wrong_dimension_signals_ignored():
    sigs = [
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE, dim=ProfileDimension.TECHNICAL_DEPTH),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE, dim=ProfileDimension.COMMUNICATION),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.ENGINEERING_JUDGMENT_HIGH not in types


def test_communication_signals_do_not_affect_judgment():
    sigs = [
        _sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.NEGATIVE, dim=_DIM),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    types = [m.pattern_type for m in result.matches]
    assert EvidenceType.ENGINEERING_JUDGMENT_HIGH not in types
    assert EvidenceType.ENGINEERING_JUDGMENT_LOW not in types


# ---- idempotency -----------------------------------------------------------

def test_idempotency_does_not_re_emit_same_signal():
    sigs = [
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
    ]
    ri = _make_input(sigs)
    result1 = DETECTOR.detect(ri)
    assert len(result1.generated_signals) > 0

    # Simulate the store already containing the generated signal.
    store = ri.interview_memory.evidence_store
    for s in result1.generated_signals:
        store = store.append(s)
    memory = ri.interview_memory.model_copy(update={"evidence_store": store})
    ri2 = ri.model_copy(update={"interview_memory": memory})
    result2 = DETECTOR.detect(ri2)
    assert len(result2.generated_signals) == 0


# ---- generated signals contract --------------------------------------------

def test_generated_signal_source_is_pattern_detector():
    sigs = [
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    for sig in result.generated_signals:
        assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_generated_signal_dimension_is_engineering_judgment():
    sigs = [
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    for sig in result.generated_signals:
        assert sig.dimension == ProfileDimension.ENGINEERING_JUDGMENT


# ---- empty evidence -------------------------------------------------------

def test_empty_evidence_no_matches_except_gap():
    result = DETECTOR.detect(_make_input([], questions_answered=1))
    assert result.matches == []
    assert result.generated_signals == []


def test_label_contains_ratio_info():
    sigs = [
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    judgment_matches = [m for m in result.matches if m.pattern_type == EvidenceType.ENGINEERING_JUDGMENT_HIGH]
    assert any("engineering_judgment" in m.label for m in judgment_matches)
