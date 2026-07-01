# tests/services/interview_reasoner/pattern_detection/detectors/test_collaboration_detector.py
"""Integration tests for CollaborationDetector."""

from __future__ import annotations

import time
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
from services.interview_reasoner.pattern_detection.detectors.collaboration_detector import (
    CollaborationDetector,
)


def _uid() -> str:
    return str(uuid.uuid4())


def _sig(
    signal_type: EvidenceType,
    polarity: EvidencePolarity = EvidencePolarity.POSITIVE,
    dim: ProfileDimension = ProfileDimension.COMMUNICATION,
    area: str = "area_a",
    q_idx: int = 1,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=_uid(),
        question_index=q_idx,
        question_area=area,
        dimension=dim,
        polarity=polarity,
        signal_type=signal_type,
        strength=0.7,
        source=EvidenceSource.PATTERN_DETECTOR,
        timestamp_question_index=q_idx,
    )


def _make_input(signals: list[EvidenceSignal], q_idx: int = 5, area: str = "collab") -> ReasonerInput:
    store = EvidenceStore(signals=signals)
    metrics = SessionMetrics(questions_answered=5)
    memory = InterviewMemory(evidence_store=store, session_metrics=metrics)
    return ReasonerInput(
        session_id="test-session",
        question_index=q_idx,
        interview_memory=memory,
        current_question_area=area,
    )


DETECTOR = CollaborationDetector()


# ---- metadata ----------------------------------------------------------------

def test_detector_name():
    assert DETECTOR.metadata.name == "CollaborationDetector"


def test_detector_priority():
    assert DETECTOR.metadata.priority == 110


def test_detector_version():
    assert DETECTOR.metadata.version == "1.0.0"


def test_detector_dependency():
    assert "LeadershipDetector" in DETECTOR.metadata.dependencies


# ---- empty / insufficient signals -------------------------------------------

def test_empty_session_returns_empty_result():
    result = DETECTOR.detect(_make_input([]))
    assert result.detector_name == "CollaborationDetector"
    assert result.matches == []
    assert result.generated_signals == []


def test_two_behavioral_signals_no_fire():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_GROWTH, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, area="b"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert result.matches == []


# ---- strong collaboration ----------------------------------------------------

def test_strong_collaborator_produces_match():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="b"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="c"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="d"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="e"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert len(result.matches) >= 1


def test_strong_collaborator_signal_is_positive():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="b"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="c"),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="d"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="e"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    if result.generated_signals:
        assert result.generated_signals[0].polarity == EvidencePolarity.POSITIVE


# ---- collaboration deficit ---------------------------------------------------

def test_collaboration_deficit_when_only_instability():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="c"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert len(result.matches) == 1
    assert result.generated_signals[0].signal_type == EvidenceType.COLLABORATION_DEFICIT


def test_collaboration_deficit_signal_is_negative():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="c"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert result.generated_signals[0].polarity == EvidencePolarity.NEGATIVE


def test_collaboration_deficit_strength_is_0_45():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="c"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert result.generated_signals[0].strength == pytest.approx(0.45)


# ---- never overwrites leadership signals ------------------------------------

def test_does_not_overwrite_leadership_signals():
    sigs = [
        _sig(EvidenceType.LEADERSHIP_STRONG, polarity=EvidencePolarity.POSITIVE, area="a"),
        _sig(EvidenceType.LEADERSHIP_EMERGING, polarity=EvidencePolarity.POSITIVE, area="b"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.COMMUNICATION, area="c"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    for sig in result.generated_signals:
        assert sig.signal_type not in (EvidenceType.LEADERSHIP_STRONG, EvidenceType.LEADERSHIP_EMERGING)


# ---- idempotency -------------------------------------------------------------

def test_idempotency_no_duplicate_signals():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="c"),
    ]
    result1 = DETECTOR.detect(_make_input(sigs))
    if result1.generated_signals:
        existing = result1.generated_signals[0]
        result2 = DETECTOR.detect(_make_input(sigs + [existing]))
        assert len(result2.generated_signals) == 0


# ---- match label format -------------------------------------------------------

def test_match_label_format():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="c"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    if result.matches:
        assert "Collaboration[" in result.matches[0].label
        assert "ratio=" in result.matches[0].label
        assert "conflict_res=" in result.matches[0].label


# ---- performance -------------------------------------------------------------

def test_performance_under_20ms_on_20_signals():
    sigs = [
        _sig(
            EvidenceType.BEHAVIORAL_GROWTH if i % 2 == 0 else EvidenceType.BEHAVIORAL_INSTABILITY,
            polarity=EvidencePolarity.POSITIVE if i % 2 == 0 else EvidencePolarity.NEGATIVE,
            dim=ProfileDimension.COMMUNICATION,
            area=f"area_{i % 5}",
            q_idx=i,
        )
        for i in range(20)
    ]
    rinput = _make_input(sigs)
    start = time.perf_counter()
    DETECTOR.detect(rinput)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 20.0, f"Performance exceeded 20ms: {elapsed_ms:.2f}ms"


# ---- determinism -------------------------------------------------------------

def test_determinism_same_input_same_verdict():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="c"),
    ]
    rinput = _make_input(sigs)
    r1 = DETECTOR.detect(rinput)
    r2 = DETECTOR.detect(rinput)
    types1 = [s.signal_type for s in r1.generated_signals]
    types2 = [s.signal_type for s in r2.generated_signals]
    assert types1 == types2
