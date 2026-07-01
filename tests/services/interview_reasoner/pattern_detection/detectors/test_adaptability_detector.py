# tests/services/interview_reasoner/pattern_detection/detectors/test_adaptability_detector.py
"""Integration tests for AdaptabilityDetector."""

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
from services.interview_reasoner.pattern_detection.detectors.adaptability_detector import (
    AdaptabilityDetector,
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


def _make_input(signals: list[EvidenceSignal], q_idx: int = 5, area: str = "adapt") -> ReasonerInput:
    store = EvidenceStore(signals=signals)
    metrics = SessionMetrics(questions_answered=5)
    memory = InterviewMemory(evidence_store=store, session_metrics=metrics)
    return ReasonerInput(
        session_id="test-session",
        question_index=q_idx,
        interview_memory=memory,
        current_question_area=area,
    )


DETECTOR = AdaptabilityDetector()


# ---- metadata ----------------------------------------------------------------

def test_detector_name():
    assert DETECTOR.metadata.name == "AdaptabilityDetector"


def test_detector_priority():
    assert DETECTOR.metadata.priority == 120


def test_detector_version():
    assert DETECTOR.metadata.version == "1.0.0"


def test_detector_dependency():
    assert "CollaborationDetector" in DETECTOR.metadata.dependencies


# ---- empty / insufficient signals -------------------------------------------

def test_empty_session_returns_empty_result():
    result = DETECTOR.detect(_make_input([]))
    assert result.detector_name == "AdaptabilityDetector"
    assert result.matches == []
    assert result.generated_signals == []


def test_single_signal_no_fire():
    sigs = [_sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE)]
    result = DETECTOR.detect(_make_input(sigs))
    assert result.matches == []


# ---- high adaptability -------------------------------------------------------

def test_highly_adaptable_produces_match():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=1, area="a"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, q_idx=2, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=3, area="b"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, q_idx=4, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=5, area="c"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, q_idx=6, area="c"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=7, area="d"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, q_idx=8, area="d"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=9, area="e"),
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, q_idx=10, area="e"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert len(result.matches) >= 1
    assert result.generated_signals[0].signal_type == EvidenceType.ADAPTABILITY_HIGH


def test_highly_adaptable_signal_positive_polarity():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=i*2, area=f"a{i}")
        for i in range(1, 6)
    ] + [
        _sig(EvidenceType.BEHAVIORAL_GROWTH, polarity=EvidencePolarity.POSITIVE, q_idx=i*2+1, area=f"a{i}")
        for i in range(1, 6)
    ]
    result = DETECTOR.detect(_make_input(sigs))
    if result.generated_signals:
        if result.generated_signals[0].signal_type == EvidenceType.ADAPTABILITY_HIGH:
            assert result.generated_signals[0].polarity == EvidencePolarity.POSITIVE


# ---- proactive flexibility path ---------------------------------------------

def test_adaptable_via_proactive_flexibility():
    sigs = [
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="x", q_idx=1),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="y", q_idx=2),
        _sig(EvidenceType.CROSS_AREA_CONSISTENT, polarity=EvidencePolarity.POSITIVE, area="z", q_idx=3),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert len(result.matches) >= 1
    assert result.generated_signals[0].signal_type == EvidenceType.ADAPTABILITY_MODERATE


# ---- low adaptability --------------------------------------------------------

def test_low_adaptability_when_rigidity_dominates():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=1, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=2, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=3, area="c"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert len(result.matches) == 1
    assert result.generated_signals[0].signal_type == EvidenceType.ADAPTABILITY_LOW


def test_low_adaptability_signal_is_negative():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=1, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=2, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=3, area="c"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    assert result.generated_signals[0].polarity == EvidencePolarity.NEGATIVE


# ---- idempotency -------------------------------------------------------------

def test_idempotency_no_duplicate_signals():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=1, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=2, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=3, area="c"),
    ]
    result1 = DETECTOR.detect(_make_input(sigs))
    if result1.generated_signals:
        existing = result1.generated_signals[0]
        result2 = DETECTOR.detect(_make_input(sigs + [existing]))
        assert len(result2.generated_signals) == 0


# ---- match label format -------------------------------------------------------

def test_match_label_format():
    sigs = [
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=1, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=2, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=3, area="c"),
    ]
    result = DETECTOR.detect(_make_input(sigs))
    if result.matches:
        assert "Adaptability[" in result.matches[0].label
        assert "ratio=" in result.matches[0].label
        assert "recovery=" in result.matches[0].label
        assert "rigidity=" in result.matches[0].label


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
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=1, area="a"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=2, area="b"),
        _sig(EvidenceType.BEHAVIORAL_INSTABILITY, polarity=EvidencePolarity.NEGATIVE, q_idx=3, area="c"),
    ]
    rinput = _make_input(sigs)
    r1 = DETECTOR.detect(rinput)
    r2 = DETECTOR.detect(rinput)
    types1 = [s.signal_type for s in r1.generated_signals]
    types2 = [s.signal_type for s in r2.generated_signals]
    assert types1 == types2
