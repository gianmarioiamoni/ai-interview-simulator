# tests/services/interview_reasoner/pattern_detection/detectors/confidence_calibration/test_analyzer.py
"""Tests for ConfidenceCalibrationAnalyzer."""

from __future__ import annotations

import pytest

from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoning_history import ReasoningEntry
from services.interview_reasoner.pattern_detection.detectors.confidence_calibration.analyzer import (
    CalibrationMetrics,
    ConfidenceCalibrationAnalyzer,
    MIN_HISTORY_LENGTH,
    SATURATION_THRESHOLD,
)


def _entry(q_idx: int, confidence: float) -> ReasoningEntry:
    return ReasoningEntry(
        question_index=q_idx,
        reasoning_confidence=confidence,
    )


ANALYZER = ConfidenceCalibrationAnalyzer()


# ---- empty / guard -----------------------------------------------------------

def test_empty_history_returns_zeroed():
    metrics = ANALYZER.analyze([])
    assert metrics.history_length == 0
    assert metrics.confidence_variance == 0.0
    assert metrics.stability_score == 1.0


def test_below_min_history_returns_partial():
    entries = [_entry(0, 0.5), _entry(1, 0.6)]
    assert len(entries) < MIN_HISTORY_LENGTH
    metrics = ANALYZER.analyze(entries)
    assert metrics.history_length == 2
    assert metrics.confidence_trend == "INSUFFICIENT"


def test_single_entry_returns_partial():
    metrics = ANALYZER.analyze([_entry(0, 0.7)])
    assert metrics.history_length == 1
    assert metrics.confidence_trend == "INSUFFICIENT"


# ---- stable confidence -------------------------------------------------------

def test_stable_confidence_low_variance():
    entries = [_entry(i, 0.7) for i in range(5)]
    metrics = ANALYZER.analyze(entries)
    assert metrics.confidence_variance == pytest.approx(0.0, abs=0.001)
    assert metrics.confidence_oscillation == pytest.approx(0.0, abs=0.001)
    assert metrics.stability_score == pytest.approx(1.0, abs=0.001)


def test_stable_trend_label():
    entries = [_entry(i, 0.6 + i * 0.01) for i in range(5)]
    metrics = ANALYZER.analyze(entries)
    assert metrics.confidence_trend == "STABLE"


# ---- rising confidence -------------------------------------------------------

def test_rising_confidence_positive_slope():
    entries = [_entry(i, 0.3 + i * 0.1) for i in range(5)]
    metrics = ANALYZER.analyze(entries)
    assert metrics.confidence_slope > 0.05
    assert metrics.confidence_trend == "RISING"


# ---- falling confidence -------------------------------------------------------

def test_falling_confidence_negative_slope():
    entries = [_entry(i, 0.9 - i * 0.1) for i in range(5)]
    metrics = ANALYZER.analyze(entries)
    assert metrics.confidence_slope < -0.05
    assert metrics.confidence_trend == "FALLING"


# ---- oscillating confidence --------------------------------------------------

def test_oscillating_confidence_high_oscillation():
    values = [0.1, 0.9, 0.1, 0.9, 0.1]
    entries = [_entry(i, v) for i, v in enumerate(values)]
    metrics = ANALYZER.analyze(entries)
    assert metrics.confidence_oscillation > 0.3
    assert metrics.confidence_trend == "OSCILLATING"


def test_oscillation_reduces_stability():
    values = [0.1, 0.9, 0.1, 0.9, 0.1]
    entries = [_entry(i, v) for i, v in enumerate(values)]
    metrics = ANALYZER.analyze(entries)
    assert metrics.stability_score < 0.5


# ---- saturation ---------------------------------------------------------------

def test_saturation_at_maximum():
    entries = [_entry(i, 1.0) for i in range(5)]
    metrics = ANALYZER.analyze(entries)
    assert metrics.confidence_saturation == pytest.approx(1.0)


def test_saturation_at_minimum():
    entries = [_entry(i, 0.0) for i in range(5)]
    metrics = ANALYZER.analyze(entries)
    assert metrics.confidence_saturation == pytest.approx(1.0)


def test_no_saturation_mid_range():
    entries = [_entry(i, 0.5) for i in range(5)]
    metrics = ANALYZER.analyze(entries)
    assert metrics.confidence_saturation == pytest.approx(0.0)


# ---- variance ----------------------------------------------------------------

def test_high_variance_values():
    values = [0.1, 0.9, 0.2, 0.8, 0.3]
    entries = [_entry(i, v) for i, v in enumerate(values)]
    metrics = ANALYZER.analyze(entries)
    assert metrics.confidence_variance > 0.05


# ---- mean confidence ---------------------------------------------------------

def test_mean_confidence_computed():
    entries = [_entry(i, 0.5) for i in range(5)]
    metrics = ANALYZER.analyze(entries)
    assert metrics.mean_confidence == pytest.approx(0.5)


def test_mean_confidence_empty():
    metrics = CalibrationMetrics()
    assert metrics.mean_confidence == 0.0


# ---- immutability ------------------------------------------------------------

def test_calibration_metrics_is_frozen():
    metrics = CalibrationMetrics(confidence_variance=0.1)
    with pytest.raises((AttributeError, TypeError)):
        metrics.confidence_variance = 99.0  # type: ignore[misc]


# ---- history_length ----------------------------------------------------------

def test_history_length_correct():
    entries = [_entry(i, 0.6) for i in range(7)]
    metrics = ANALYZER.analyze(entries)
    assert metrics.history_length == 7
