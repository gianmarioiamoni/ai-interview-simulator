# services/interview_reasoner/pattern_detection/detectors/confidence_calibration_detector.py
"""ConfidenceCalibrationDetector — reasoning pipeline quality detector (M2-7K, DET-10).

This detector evaluates the QUALITY OF THE REASONING PIPELINE — NOT the candidate.
It assesses whether the reasoning_confidence values emitted by the Reasoner across the
session are trustworthy, stable, and well-calibrated.

Reads: ReasonerInput.interview_memory.reasoning_history.entries[].reasoning_confidence
Does NOT read: EvidenceStore signals, CandidateProfile dimension scores.

priority = 90
dependencies = ["ConsistencyAcrossInterviewDetector"]

Signals emitted:
  CONFIDENCE_WELL_CALIBRATED — confidence track is stable and accurate
  CONFIDENCE_OVERCONFIDENT   — confidence exceeds actual performance
  CONFIDENCE_UNDERCONFIDENT  — confidence below actual performance
  CONFIDENCE_UNSTABLE        — oscillating or erratic confidence track
  CONFIDENCE_SATURATED       — reserved (not emitted in V1.1; prepared for V1.2)

CalibrationIssue objects are produced alongside signals for future V1.2 CoachingEngine use.
They are stored in warnings (serialized) per DDS convention.

Deterministic; O(h) where h = history length; no LLM; no external services.
"""

from __future__ import annotations

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.pattern_match import PatternMatch
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.detectors.confidence_calibration.analyzer import (
    ConfidenceCalibrationAnalyzer,
    MIN_HISTORY_LENGTH,
)
from services.interview_reasoner.pattern_detection.detectors.confidence_calibration.scorer import (
    CalibrationVerdict,
    ConfidenceCalibrationScorer,
)
from services.interview_reasoner.pattern_detection.detectors.confidence_calibration.signal_factory import (
    ConfidenceCalibrationSignalFactory,
)
from services.interview_reasoner.pattern_detection.signal_idempotency import filter_new_signals

_METADATA = DetectorMetadata(
    name="ConfidenceCalibrationDetector",
    version="1.0.0",
    priority=90,
    enabled=True,
    dependencies=["ConsistencyAcrossInterviewDetector"],
)


class ConfidenceCalibrationDetector(PatternDetector):
    """Detect reasoning pipeline confidence calibration quality."""

    def __init__(self) -> None:
        self._analyzer = ConfidenceCalibrationAnalyzer()
        self._scorer = ConfidenceCalibrationScorer()
        self._factory = ConfidenceCalibrationSignalFactory()

    @property
    def metadata(self) -> DetectorMetadata:
        return _METADATA

    def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
        history = reasoner_input.interview_memory.reasoning_history
        store = reasoner_input.interview_memory.evidence_store
        q_idx = reasoner_input.question_index
        area = reasoner_input.current_question_area or "unknown"

        metrics = self._analyzer.analyze(list(history.entries))

        if metrics.history_length < MIN_HISTORY_LENGTH:
            return DetectorResult(detector_name=_METADATA.name)

        verdict = self._scorer.score(metrics)
        signal, issue = self._factory.create(verdict, metrics, q_idx, area)

        candidates = [signal] if signal is not None else []
        new_signals = filter_new_signals(candidates, store)

        matches: list[PatternMatch] = []
        warnings: list[str] = []

        if signal is not None:
            matches.append(PatternMatch(
                pattern_type=signal.signal_type,
                evidence_signals=[signal],
                label=(
                    f"Calibration[{verdict.value}]: "
                    f"mean={metrics.mean_confidence:.2f}, "
                    f"stability={metrics.stability_score:.2f}, "
                    f"osc={metrics.confidence_oscillation:.2f}"
                ),
            ))

        if issue is not None:
            warnings.append(
                f"CalibrationIssue[{issue.severity}]: {issue.reason} "
                f"(delta={issue.confidence_delta:.3f}, "
                f"action={issue.recommended_action})"
            )

        return DetectorResult(
            detector_name=_METADATA.name,
            matches=matches,
            generated_signals=new_signals,
            warnings=warnings,
        )
