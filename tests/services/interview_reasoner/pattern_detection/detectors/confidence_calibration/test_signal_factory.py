# tests/services/interview_reasoner/pattern_detection/detectors/confidence_calibration/test_signal_factory.py
"""Tests for ConfidenceCalibrationSignalFactory and CalibrationIssue."""

from __future__ import annotations

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.confidence_calibration.analyzer import (
    CalibrationMetrics,
)
from services.interview_reasoner.pattern_detection.detectors.confidence_calibration.scorer import (
    CalibrationVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.confidence_calibration.signal_factory import (
    CalibrationIssue,
    ConfidenceCalibrationSignalFactory,
)

FACTORY = ConfidenceCalibrationSignalFactory()


def _metrics(
    history: tuple[float, ...] = (0.6, 0.65, 0.6),
    variance: float = 0.001,
    oscillation: float = 0.05,
    saturation: float = 0.0,
    stability: float = 0.95,
    length: int = 3,
) -> CalibrationMetrics:
    return CalibrationMetrics(
        confidence_history=history,
        confidence_variance=variance,
        confidence_oscillation=oscillation,
        confidence_saturation=saturation,
        stability_score=stability,
        history_length=length,
    )


# ---- WELL_CALIBRATED ---------------------------------------------------------

def test_well_calibrated_returns_signal():
    sig, issue = FACTORY.create(CalibrationVerdict.WELL_CALIBRATED, _metrics(), 3, "area")
    assert sig is not None
    assert sig.signal_type == EvidenceType.CONFIDENCE_WELL_CALIBRATED


def test_well_calibrated_no_issue():
    _, issue = FACTORY.create(CalibrationVerdict.WELL_CALIBRATED, _metrics(), 3, "area")
    assert issue is None


def test_well_calibrated_positive_polarity():
    sig, _ = FACTORY.create(CalibrationVerdict.WELL_CALIBRATED, _metrics(), 3, "area")
    assert sig.polarity == EvidencePolarity.POSITIVE


def test_well_calibrated_dimension_technical_depth():
    sig, _ = FACTORY.create(CalibrationVerdict.WELL_CALIBRATED, _metrics(), 3, "area")
    assert sig.dimension == ProfileDimension.TECHNICAL_DEPTH


# ---- SLIGHTLY_OVERCONFIDENT --------------------------------------------------

def test_slightly_overconfident_signal_type():
    m = _metrics(history=(0.82, 0.84, 0.83))
    sig, _ = FACTORY.create(CalibrationVerdict.SLIGHTLY_OVERCONFIDENT, m, 3, "area")
    assert sig.signal_type == EvidenceType.CONFIDENCE_OVERCONFIDENT


def test_slightly_overconfident_produces_issue():
    m = _metrics(history=(0.82, 0.84, 0.83))
    _, issue = FACTORY.create(CalibrationVerdict.SLIGHTLY_OVERCONFIDENT, m, 3, "area")
    assert issue is not None
    assert issue.severity == "LOW"


def test_slightly_overconfident_negative_polarity():
    m = _metrics(history=(0.82, 0.84, 0.83))
    sig, _ = FACTORY.create(CalibrationVerdict.SLIGHTLY_OVERCONFIDENT, m, 3, "area")
    assert sig.polarity == EvidencePolarity.NEGATIVE


# ---- OVERCONFIDENT -----------------------------------------------------------

def test_overconfident_signal_type():
    m = _metrics(history=(0.95, 0.96, 0.95))
    sig, _ = FACTORY.create(CalibrationVerdict.OVERCONFIDENT, m, 3, "area")
    assert sig.signal_type == EvidenceType.CONFIDENCE_OVERCONFIDENT


def test_overconfident_produces_high_severity_issue():
    m = _metrics(history=(0.95, 0.96, 0.95))
    _, issue = FACTORY.create(CalibrationVerdict.OVERCONFIDENT, m, 3, "area")
    assert issue is not None
    assert issue.severity == "HIGH"


# ---- UNDERCONFIDENT ----------------------------------------------------------

def test_underconfident_signal_type():
    m = _metrics(history=(0.1, 0.15, 0.12))
    sig, _ = FACTORY.create(CalibrationVerdict.UNDERCONFIDENT, m, 3, "area")
    assert sig.signal_type == EvidenceType.CONFIDENCE_UNDERCONFIDENT


def test_underconfident_negative_polarity():
    m = _metrics(history=(0.1, 0.15, 0.12))
    sig, _ = FACTORY.create(CalibrationVerdict.UNDERCONFIDENT, m, 3, "area")
    assert sig.polarity == EvidencePolarity.NEGATIVE


def test_underconfident_produces_medium_severity_issue():
    m = _metrics(history=(0.1, 0.15, 0.12))
    _, issue = FACTORY.create(CalibrationVerdict.UNDERCONFIDENT, m, 3, "area")
    assert issue.severity == "MEDIUM"


# ---- UNSTABLE_CONFIDENCE -----------------------------------------------------

def test_unstable_signal_type():
    m = _metrics(oscillation=0.5, stability=0.3, history=(0.1, 0.9, 0.1))
    sig, _ = FACTORY.create(CalibrationVerdict.UNSTABLE_CONFIDENCE, m, 3, "area")
    assert sig.signal_type == EvidenceType.CONFIDENCE_UNSTABLE


def test_unstable_produces_high_severity_issue():
    m = _metrics(oscillation=0.5, stability=0.3, history=(0.1, 0.9, 0.1))
    _, issue = FACTORY.create(CalibrationVerdict.UNSTABLE_CONFIDENCE, m, 3, "area")
    assert issue.severity == "HIGH"


def test_unstable_strength_equals_oscillation():
    m = _metrics(oscillation=0.5, stability=0.3, history=(0.1, 0.9, 0.1))
    sig, _ = FACTORY.create(CalibrationVerdict.UNSTABLE_CONFIDENCE, m, 3, "area")
    assert sig.strength == pytest.approx(0.5, abs=0.01)


# ---- CalibrationIssue immutability ------------------------------------------

def test_calibration_issue_is_frozen():
    issue = CalibrationIssue(
        severity="HIGH",
        reason="test",
        affected_questions=5,
        confidence_delta=0.3,
        recommended_action="none",
    )
    with pytest.raises((AttributeError, TypeError)):
        issue.severity = "LOW"  # type: ignore[misc]


# ---- source and metadata ----------------------------------------------------

def test_signal_source_is_pattern_detector():
    sig, _ = FACTORY.create(CalibrationVerdict.WELL_CALIBRATED, _metrics(), 3, "area")
    assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_signal_ids_unique():
    sig1, _ = FACTORY.create(CalibrationVerdict.WELL_CALIBRATED, _metrics(), 3, "area")
    sig2, _ = FACTORY.create(CalibrationVerdict.WELL_CALIBRATED, _metrics(), 3, "area")
    assert sig1.id != sig2.id


def test_signal_area_correct():
    sig, _ = FACTORY.create(CalibrationVerdict.WELL_CALIBRATED, _metrics(), 3, "calibration_area")
    assert sig.question_area == "calibration_area"


def test_never_generates_candidate_quality_signals():
    forbidden = {
        EvidenceType.LEADERSHIP_STRONG, EvidenceType.LEADERSHIP_EMERGING,
        EvidenceType.COLLABORATION_STRONG, EvidenceType.COLLABORATION_EFFECTIVE,
        EvidenceType.ADAPTABILITY_HIGH, EvidenceType.BEHAVIORAL_GROWTH,
    }
    for verdict in CalibrationVerdict:
        sig, _ = FACTORY.create(verdict, _metrics(), 1, "area")
        if sig is not None:
            assert sig.signal_type not in forbidden
