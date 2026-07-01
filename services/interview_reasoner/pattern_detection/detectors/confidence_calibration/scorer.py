# services/interview_reasoner/pattern_detection/detectors/confidence_calibration/scorer.py
"""ConfidenceCalibrationScorer — threshold verdicts for calibration metrics (M2-7K, DET-10).

Evaluates the REASONING PIPELINE quality — not the candidate's ability.

Thresholds (frozen constants):
  WELL_CALIBRATED       : stability >= 0.7 AND variance <= 0.05 AND saturation <= 0.3
  SLIGHTLY_OVERCONFIDENT: mean_confidence > OVERCONFIDENT_THRESHOLD but < SATURATED_THRESHOLD
  OVERCONFIDENT         : mean_confidence >= SATURATED_THRESHOLD (near-saturated high)
  UNDERCONFIDENT        : mean_confidence <= UNDERCONFIDENT_THRESHOLD
  UNSTABLE_CONFIDENCE   : oscillation > UNSTABLE_OSCILLATION_THRESHOLD

Verdict precedence: UNSTABLE > OVERCONFIDENT > UNDERCONFIDENT > SLIGHTLY_OVERCONFIDENT > WELL_CALIBRATED.
Guard: Returns WELL_CALIBRATED when history_length < MIN_HISTORY_LENGTH (silent, not erroneous).
Deterministic; no randomness.
"""

from __future__ import annotations

from enum import Enum

from services.interview_reasoner.pattern_detection.detectors.confidence_calibration.analyzer import (
    CalibrationMetrics,
    MIN_HISTORY_LENGTH,
)

WELL_CALIBRATED_MIN_STABILITY   = 0.70
WELL_CALIBRATED_MAX_VARIANCE    = 0.05
WELL_CALIBRATED_MAX_SATURATION  = 0.30
OVERCONFIDENT_THRESHOLD         = 0.80  # mean confidence above this → overconfident
SATURATED_THRESHOLD             = 0.92  # mean confidence above this → fully overconfident
UNDERCONFIDENT_THRESHOLD        = 0.25  # mean confidence below this → underconfident
UNSTABLE_OSCILLATION_THRESHOLD  = 0.30  # oscillation above this → unstable


class CalibrationVerdict(str, Enum):
    WELL_CALIBRATED        = "WELL_CALIBRATED"
    SLIGHTLY_OVERCONFIDENT = "SLIGHTLY_OVERCONFIDENT"
    OVERCONFIDENT          = "OVERCONFIDENT"
    UNDERCONFIDENT         = "UNDERCONFIDENT"
    UNSTABLE_CONFIDENCE    = "UNSTABLE_CONFIDENCE"


class ConfidenceCalibrationScorer:
    """Converts CalibrationMetrics into CalibrationVerdict. Pure deterministic function."""

    def score(self, metrics: CalibrationMetrics) -> CalibrationVerdict:
        """Return verdict. WELL_CALIBRATED when guard conditions are not met."""
        if metrics.history_length < MIN_HISTORY_LENGTH:
            return CalibrationVerdict.WELL_CALIBRATED

        # Check instability first (highest priority concern).
        if metrics.confidence_oscillation > UNSTABLE_OSCILLATION_THRESHOLD:
            return CalibrationVerdict.UNSTABLE_CONFIDENCE

        mean = metrics.mean_confidence

        # Full overconfidence (saturation at top).
        if mean >= SATURATED_THRESHOLD:
            return CalibrationVerdict.OVERCONFIDENT

        # Underconfidence.
        if mean <= UNDERCONFIDENT_THRESHOLD:
            return CalibrationVerdict.UNDERCONFIDENT

        # Slight overconfidence.
        if mean > OVERCONFIDENT_THRESHOLD:
            return CalibrationVerdict.SLIGHTLY_OVERCONFIDENT

        # Well-calibrated: check stability and variance explicitly.
        if (
            metrics.stability_score >= WELL_CALIBRATED_MIN_STABILITY
            and metrics.confidence_variance <= WELL_CALIBRATED_MAX_VARIANCE
            and metrics.confidence_saturation <= WELL_CALIBRATED_MAX_SATURATION
        ):
            return CalibrationVerdict.WELL_CALIBRATED

        return CalibrationVerdict.WELL_CALIBRATED
