# services/interview_reasoner/pattern_detection/detectors/confidence_calibration/signal_factory.py
"""ConfidenceCalibrationSignalFactory — produces EvidenceSignals + CalibrationIssues (M2-7K, DET-10).

Signal mapping:
  WELL_CALIBRATED        → CONFIDENCE_WELL_CALIBRATED / POSITIVE / strength = stability_score
  SLIGHTLY_OVERCONFIDENT → CONFIDENCE_OVERCONFIDENT   / NEGATIVE / strength = mean_confidence - 0.8
  OVERCONFIDENT          → CONFIDENCE_OVERCONFIDENT   / NEGATIVE / strength = min(1.0, (mean - 0.8)*3)
  UNDERCONFIDENT         → CONFIDENCE_UNDERCONFIDENT  / NEGATIVE / strength = 0.25 - mean_confidence
  UNSTABLE_CONFIDENCE    → CONFIDENCE_UNSTABLE        / NEGATIVE / strength = oscillation

CalibrationIssue is a detector-local immutable dataclass. Not a generic framework.
Architecture prepared for V1.2 integration with calibration settings (ADR-068).
Dimension: ProfileDimension.TECHNICAL_DEPTH (calibration proxies overall pipeline quality).

Never generates candidate quality signals (behavioral, leadership, collaboration, adaptability).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.confidence_calibration.analyzer import (
    CalibrationMetrics,
)
from services.interview_reasoner.pattern_detection.detectors.confidence_calibration.scorer import (
    CalibrationVerdict,
)


@dataclass(frozen=True)
class CalibrationIssue:
    """Detector-local immutable record of a detected calibration problem.

    Architecture prepared for V1.2 CalibrationFeature + CoachingEngine integration (ADR-068).
    Do NOT use as a generic framework outside ConfidenceCalibrationDetector.
    """

    severity: str               # "LOW" | "MEDIUM" | "HIGH"
    reason: str                 # human-readable explanation (pipeline-facing, not candidate-facing)
    affected_questions: int     # number of questions involved in the issue
    confidence_delta: float     # magnitude of the calibration problem
    recommended_action: str     # future CoachingEngine hint (V1.2)


class ConfidenceCalibrationSignalFactory:
    """Creates EvidenceSignals and CalibrationIssues from CalibrationVerdict."""

    def create(
        self,
        verdict: CalibrationVerdict,
        metrics: CalibrationMetrics,
        question_index: int,
        area: str,
    ) -> tuple[EvidenceSignal | None, CalibrationIssue | None]:
        """Return (EvidenceSignal | None, CalibrationIssue | None) for the verdict."""
        mean = metrics.mean_confidence

        if verdict == CalibrationVerdict.WELL_CALIBRATED:
            sig = EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.TECHNICAL_DEPTH,
                polarity=EvidencePolarity.POSITIVE,
                signal_type=EvidenceType.CONFIDENCE_WELL_CALIBRATED,
                strength=round(min(1.0, metrics.stability_score), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
            return sig, None

        if verdict == CalibrationVerdict.SLIGHTLY_OVERCONFIDENT:
            delta = round(min(1.0, mean - 0.80), 4)
            sig = EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.TECHNICAL_DEPTH,
                polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.CONFIDENCE_OVERCONFIDENT,
                strength=max(0.0, delta),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
            issue = CalibrationIssue(
                severity="LOW",
                reason="Reasoning confidence slightly above expected calibration range",
                affected_questions=metrics.history_length,
                confidence_delta=delta,
                recommended_action="Monitor; adjust confidence decay in next cycle if sustained",
            )
            return sig, issue

        if verdict == CalibrationVerdict.OVERCONFIDENT:
            delta = round(min(1.0, (mean - 0.80) * 3), 4)
            sig = EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.TECHNICAL_DEPTH,
                polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.CONFIDENCE_OVERCONFIDENT,
                strength=max(0.0, delta),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
            issue = CalibrationIssue(
                severity="HIGH",
                reason="Reasoning confidence saturated; pipeline signal is unreliable",
                affected_questions=metrics.history_length,
                confidence_delta=delta,
                recommended_action="Trigger confidence reset or recalibration step in V1.2",
            )
            return sig, issue

        if verdict == CalibrationVerdict.UNDERCONFIDENT:
            delta = round(min(1.0, 0.25 - mean), 4)
            sig = EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.TECHNICAL_DEPTH,
                polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.CONFIDENCE_UNDERCONFIDENT,
                strength=max(0.0, delta),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
            issue = CalibrationIssue(
                severity="MEDIUM",
                reason="Reasoning confidence persistently low; pipeline may lack evidence",
                affected_questions=metrics.history_length,
                confidence_delta=delta,
                recommended_action="Increase evidence collection before next cycle",
            )
            return sig, issue

        if verdict == CalibrationVerdict.UNSTABLE_CONFIDENCE:
            sig = EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.TECHNICAL_DEPTH,
                polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.CONFIDENCE_UNSTABLE,
                strength=round(min(1.0, metrics.confidence_oscillation), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
            issue = CalibrationIssue(
                severity="HIGH",
                reason="Confidence track is oscillating; pipeline reasoning is inconsistent",
                affected_questions=metrics.history_length,
                confidence_delta=round(metrics.confidence_oscillation, 4),
                recommended_action="Investigate signal quality; review EvidenceStore for contradictions",
            )
            return sig, issue

        return None, None
