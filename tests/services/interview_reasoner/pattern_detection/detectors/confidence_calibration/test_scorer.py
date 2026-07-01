# tests/services/interview_reasoner/pattern_detection/detectors/confidence_calibration/test_scorer.py
"""Tests for ConfidenceCalibrationScorer."""

from __future__ import annotations

import pytest

from services.interview_reasoner.pattern_detection.detectors.confidence_calibration.analyzer import (
    CalibrationMetrics,
    MIN_HISTORY_LENGTH,
)
from services.interview_reasoner.pattern_detection.detectors.confidence_calibration.scorer import (
    CalibrationVerdict,
    ConfidenceCalibrationScorer,
    OVERCONFIDENT_THRESHOLD,
    SATURATED_THRESHOLD,
    UNDERCONFIDENT_THRESHOLD,
    UNSTABLE_OSCILLATION_THRESHOLD,
    WELL_CALIBRATED_MIN_STABILITY,
    WELL_CALIBRATED_MAX_VARIANCE,
)

SCORER = ConfidenceCalibrationScorer()


def _metrics(
    history: tuple[float, ...] = (0.6, 0.65, 0.6),
    variance: float = 0.001,
    slope: float = 0.0,
    oscillation: float = 0.05,
    saturation: float = 0.0,
    stability: float = 0.95,
    length: int = 3,
) -> CalibrationMetrics:
    return CalibrationMetrics(
        confidence_history=history,
        confidence_variance=variance,
        confidence_slope=slope,
        confidence_oscillation=oscillation,
        confidence_saturation=saturation,
        stability_score=stability,
        history_length=length,
    )


# ---- guard -------------------------------------------------------------------

def test_well_calibrated_when_insufficient_history():
    m = _metrics(length=MIN_HISTORY_LENGTH - 1)
    assert SCORER.score(m) == CalibrationVerdict.WELL_CALIBRATED


# ---- WELL_CALIBRATED ---------------------------------------------------------

def test_well_calibrated_stable_low_variance():
    m = _metrics(variance=0.01, oscillation=0.05, stability=0.95, saturation=0.1,
                 history=(0.6, 0.62, 0.61))
    assert SCORER.score(m) == CalibrationVerdict.WELL_CALIBRATED


def test_well_calibrated_at_exact_thresholds():
    m = _metrics(
        history=(0.6, 0.62, 0.61),
        variance=WELL_CALIBRATED_MAX_VARIANCE,
        oscillation=0.05,
        stability=WELL_CALIBRATED_MIN_STABILITY,
        saturation=0.3,
    )
    assert SCORER.score(m) == CalibrationVerdict.WELL_CALIBRATED


# ---- UNSTABLE_CONFIDENCE -----------------------------------------------------

def test_unstable_when_high_oscillation():
    m = _metrics(oscillation=UNSTABLE_OSCILLATION_THRESHOLD + 0.01, stability=0.3,
                 history=(0.1, 0.9, 0.1))
    assert SCORER.score(m) == CalibrationVerdict.UNSTABLE_CONFIDENCE


def test_unstable_takes_priority_over_overconfident():
    # High mean AND high oscillation → UNSTABLE wins
    m = _metrics(oscillation=0.5, stability=0.2,
                 history=(0.95, 0.1, 0.95))
    assert SCORER.score(m) == CalibrationVerdict.UNSTABLE_CONFIDENCE


# ---- OVERCONFIDENT -----------------------------------------------------------

def test_overconfident_when_mean_above_saturated():
    h = tuple([0.95] * 5)
    m = _metrics(history=h, oscillation=0.01, stability=0.99, saturation=1.0, length=5)
    assert SCORER.score(m) == CalibrationVerdict.OVERCONFIDENT


def test_overconfident_at_exact_saturated_threshold():
    h = (SATURATED_THRESHOLD, SATURATED_THRESHOLD, SATURATED_THRESHOLD)
    m = _metrics(history=h, oscillation=0.0, stability=1.0, saturation=1.0)
    assert SCORER.score(m) == CalibrationVerdict.OVERCONFIDENT


# ---- UNDERCONFIDENT ----------------------------------------------------------

def test_underconfident_when_mean_below_threshold():
    h = (0.1, 0.15, 0.1)
    m = _metrics(history=h, oscillation=0.05, stability=0.95)
    assert SCORER.score(m) == CalibrationVerdict.UNDERCONFIDENT


def test_underconfident_at_exact_threshold():
    h = (UNDERCONFIDENT_THRESHOLD, UNDERCONFIDENT_THRESHOLD, UNDERCONFIDENT_THRESHOLD)
    m = _metrics(history=h, oscillation=0.0, stability=1.0)
    assert SCORER.score(m) == CalibrationVerdict.UNDERCONFIDENT


# ---- SLIGHTLY_OVERCONFIDENT --------------------------------------------------

def test_slightly_overconfident_above_overconfident_threshold():
    h = (0.82, 0.85, 0.83)
    m = _metrics(history=h, oscillation=0.03, stability=0.97, saturation=0.0)
    assert SCORER.score(m) == CalibrationVerdict.SLIGHTLY_OVERCONFIDENT


# ---- determinism -------------------------------------------------------------

def test_same_input_same_output():
    m = _metrics()
    assert SCORER.score(m) == SCORER.score(m)


def test_verdict_enum_values():
    assert CalibrationVerdict.WELL_CALIBRATED == "WELL_CALIBRATED"
    assert CalibrationVerdict.SLIGHTLY_OVERCONFIDENT == "SLIGHTLY_OVERCONFIDENT"
    assert CalibrationVerdict.OVERCONFIDENT == "OVERCONFIDENT"
    assert CalibrationVerdict.UNDERCONFIDENT == "UNDERCONFIDENT"
    assert CalibrationVerdict.UNSTABLE_CONFIDENCE == "UNSTABLE_CONFIDENCE"
