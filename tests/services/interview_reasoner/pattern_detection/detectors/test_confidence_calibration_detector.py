# tests/services/interview_reasoner/pattern_detection/detectors/test_confidence_calibration_detector.py
"""Integration tests for ConfidenceCalibrationDetector."""

from __future__ import annotations

import time

import pytest

from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.reasoning_history import ReasoningEntry, ReasoningHistory
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.reasoning.session_metrics import SessionMetrics
from services.interview_reasoner.pattern_detection.detectors.confidence_calibration_detector import (
    ConfidenceCalibrationDetector,
)


def _entry(q_idx: int, confidence: float) -> ReasoningEntry:
    return ReasoningEntry(question_index=q_idx, reasoning_confidence=confidence)


def _make_input(
    confidences: list[float],
    q_idx: int = 5,
    area: str = "calibration",
) -> ReasonerInput:
    entries = [_entry(i, c) for i, c in enumerate(confidences)]
    history = ReasoningHistory(entries=entries)
    store = EvidenceStore(signals=[])
    metrics = SessionMetrics(questions_answered=len(confidences))
    memory = InterviewMemory(
        evidence_store=store,
        reasoning_history=history,
        session_metrics=metrics,
    )
    return ReasonerInput(
        session_id="test-session",
        question_index=q_idx,
        interview_memory=memory,
        current_question_area=area,
    )


DETECTOR = ConfidenceCalibrationDetector()


# ---- metadata ----------------------------------------------------------------

def test_detector_name():
    assert DETECTOR.metadata.name == "ConfidenceCalibrationDetector"


def test_detector_priority():
    assert DETECTOR.metadata.priority == 90


def test_detector_version():
    assert DETECTOR.metadata.version == "1.0.0"


def test_detector_dependency():
    assert "ConsistencyAcrossInterviewDetector" in DETECTOR.metadata.dependencies


# ---- empty / insufficient ---------------------------------------------------

def test_empty_history_returns_empty_result():
    result = DETECTOR.detect(_make_input([]))
    assert result.matches == []
    assert result.generated_signals == []


def test_two_entries_no_fire():
    result = DETECTOR.detect(_make_input([0.6, 0.65]))
    assert result.matches == []


# ---- stable confidence -------------------------------------------------------

def test_stable_confidence_produces_well_calibrated():
    result = DETECTOR.detect(_make_input([0.6, 0.62, 0.61, 0.60, 0.63]))
    assert len(result.matches) >= 1
    assert result.generated_signals[0].signal_type == EvidenceType.CONFIDENCE_WELL_CALIBRATED


def test_well_calibrated_signal_positive():
    result = DETECTOR.detect(_make_input([0.6, 0.62, 0.61, 0.60, 0.63]))
    from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
    if result.generated_signals:
        assert result.generated_signals[0].polarity == EvidencePolarity.POSITIVE


# ---- confidence inflation / overconfident ------------------------------------

def test_overconfident_produces_match():
    result = DETECTOR.detect(_make_input([0.95, 0.96, 0.97, 0.98, 0.97]))
    assert len(result.matches) >= 1
    assert result.generated_signals[0].signal_type == EvidenceType.CONFIDENCE_OVERCONFIDENT


def test_overconfident_produces_warning():
    result = DETECTOR.detect(_make_input([0.95, 0.96, 0.97, 0.98, 0.97]))
    assert len(result.warnings) >= 1
    assert "HIGH" in result.warnings[0]


# ---- confidence collapse / underconfident ------------------------------------

def test_underconfident_produces_match():
    result = DETECTOR.detect(_make_input([0.1, 0.12, 0.08, 0.1, 0.11]))
    assert len(result.matches) >= 1
    assert result.generated_signals[0].signal_type == EvidenceType.CONFIDENCE_UNDERCONFIDENT


# ---- oscillation -------------------------------------------------------------

def test_oscillating_confidence_produces_unstable():
    result = DETECTOR.detect(_make_input([0.1, 0.9, 0.1, 0.9, 0.1]))
    assert len(result.matches) >= 1
    assert result.generated_signals[0].signal_type == EvidenceType.CONFIDENCE_UNSTABLE


def test_unstable_produces_warning():
    result = DETECTOR.detect(_make_input([0.1, 0.9, 0.1, 0.9, 0.1]))
    assert any("HIGH" in w for w in result.warnings)


# ---- idempotency -------------------------------------------------------------

def test_idempotency_no_duplicate_signals():
    confidences = [0.95, 0.96, 0.97, 0.98, 0.97]
    result1 = DETECTOR.detect(_make_input(confidences))
    if result1.generated_signals:
        existing = result1.generated_signals[0]
        # Build new input with the existing signal in the store
        entries = [_entry(i, c) for i, c in enumerate(confidences)]
        history = ReasoningHistory(entries=entries)
        store = EvidenceStore(signals=[existing])
        metrics = SessionMetrics(questions_answered=5)
        memory = InterviewMemory(evidence_store=store, reasoning_history=history, session_metrics=metrics)
        rinput2 = ReasonerInput(
            session_id="test-session",
            question_index=5,
            interview_memory=memory,
            current_question_area="area",
        )
        result2 = DETECTOR.detect(rinput2)
        assert len(result2.generated_signals) == 0


# ---- match label format -------------------------------------------------------

def test_match_label_format():
    result = DETECTOR.detect(_make_input([0.6, 0.62, 0.61, 0.60, 0.63]))
    if result.matches:
        label = result.matches[0].label
        assert "Calibration[" in label
        assert "mean=" in label
        assert "stability=" in label
        assert "osc=" in label


# ---- performance -------------------------------------------------------------

def test_performance_under_10ms_on_20_entries():
    confidences = [0.5 + (i % 3) * 0.1 for i in range(20)]
    rinput = _make_input(confidences)
    start = time.perf_counter()
    DETECTOR.detect(rinput)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 10.0, f"Performance exceeded 10ms: {elapsed_ms:.2f}ms"


# ---- determinism -------------------------------------------------------------

def test_determinism_same_input_same_verdict():
    confidences = [0.1, 0.9, 0.1, 0.9, 0.1]
    rinput = _make_input(confidences)
    r1 = DETECTOR.detect(rinput)
    r2 = DETECTOR.detect(rinput)
    types1 = [s.signal_type for s in r1.generated_signals]
    types2 = [s.signal_type for s in r2.generated_signals]
    assert types1 == types2


# ---- does not evaluate candidate quality ------------------------------------

def test_no_candidate_quality_signals_emitted():
    forbidden = {
        EvidenceType.BEHAVIORAL_GROWTH, EvidenceType.LEADERSHIP_STRONG,
        EvidenceType.COLLABORATION_EFFECTIVE, EvidenceType.ADAPTABILITY_HIGH,
        EvidenceType.REASONING_DEPTH_HIGH, EvidenceType.ENGINEERING_JUDGMENT_HIGH,
    }
    result = DETECTOR.detect(_make_input([0.6, 0.65, 0.7, 0.68, 0.69]))
    for sig in result.generated_signals:
        assert sig.signal_type not in forbidden
