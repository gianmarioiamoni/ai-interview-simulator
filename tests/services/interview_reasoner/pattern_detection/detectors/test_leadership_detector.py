# tests/services/interview_reasoner/pattern_detection/detectors/test_leadership_detector.py
"""Integration tests for LeadershipDetector."""

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
from services.interview_reasoner.pattern_detection.detectors.leadership_detector import (
    LeadershipDetector,
)


def _uid() -> str:
    return str(uuid.uuid4())


def _sig(
    signal_type: EvidenceType,
    polarity: EvidencePolarity = EvidencePolarity.POSITIVE,
    dim: ProfileDimension = ProfileDimension.PROBLEM_SOLVING,
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


def _make_input(signals: list[EvidenceSignal], q_idx: int = 5, area: str = "behavior") -> ReasonerInput:
    store = EvidenceStore(signals=signals)
    metrics = SessionMetrics(questions_answered=5)
    memory = InterviewMemory(
        evidence_store=store,
        session_metrics=metrics,
    )
    return ReasonerInput(
        session_id="test-session",
        question_index=q_idx,
        interview_memory=memory,
        current_question_area=area,
    )


DETECTOR = LeadershipDetector()


# ---- metadata ----------------------------------------------------------------

def test_detector_name():
    assert DETECTOR.metadata.name == "LeadershipDetector"


def test_detector_priority():
    assert DETECTOR.metadata.priority == 100


def test_detector_version():
    assert DETECTOR.metadata.version == "1.0.0"


def test_detector_dependency():
    assert "ConsistencyAcrossInterviewDetector" in DETECTOR.metadata.dependencies


# ---- empty / insufficient signals -------------------------------------------

def test_empty_session_returns_empty_result():
    result = DETECTOR.detect(_make_input([]))
    assert result.detector_name == "LeadershipDetector"
    assert result.matches == []
    assert result.generated_signals == []


def test_two_behavioral_signals_no_fire():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_GROWTH, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, area="b"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert result.matches == []


# ---- positive leadership -----------------------------------------------------

def test_strong_leader_produces_match():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="a", q_idx=1),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="b", q_idx=2),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="c", q_idx=3),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="d", q_idx=4),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="e", q_idx=5),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert len(result.matches) >= 1


def test_strong_leader_signal_type():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="b"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="c"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="d"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE,
             dim=ProfileDimension.PROBLEM_SOLVING, area="e"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    if result.generated_signals:
        assert result.generated_signals[0].signal_type in (
            EvidenceType.LEADERSHIP_STRONG,
            EvidenceType.LEADERSHIP_EMERGING,
        )


# ---- absent leadership -------------------------------------------------------

def test_leadership_absent_when_only_instability():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="c"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert len(result.matches) == 1
    assert result.generated_signals[0].signal_type == EvidenceType.LEADERSHIP_ABSENT


def test_leadership_absent_signal_is_negative():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="c"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert result.generated_signals[0].polarity == EvidencePolarity.NEGATIVE


def test_leadership_absent_strength_is_0_4():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="c"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert result.generated_signals[0].strength == pytest.approx(0.4)


# ---- idempotency -------------------------------------------------------------

def test_idempotency_no_duplicate_signals():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, area="c"),
    ]
    result1 = DETECTOR.detect(_make_input(sigs))
    # Simulate signal already present in store
    if result1.generated_signals:
        existing = result1.generated_signals[0]
        sigs_with_existing = sigs + [existing]
        result2 = DETECTOR.detect(_make_input(sigs_with_existing))
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
        assert "Leadership[" in result.matches[0].label
        assert "ratio=" in result.matches[0].label
        assert "dims=" in result.matches[0].label


# ---- performance -------------------------------------------------------------

def test_performance_under_20ms_on_20_signals():
    sigs = [
        _sig(
            EvidenceType.BEHAVIORAL_GROWTH if i % 2 == 0 else EvidenceType.BEHAVIORAL_INSTABILITY,
            polarity=EvidencePolarity.POSITIVE if i % 2 == 0 else EvidencePolarity.NEGATIVE,
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
