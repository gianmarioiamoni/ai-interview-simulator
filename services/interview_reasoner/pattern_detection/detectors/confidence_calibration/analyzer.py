# services/interview_reasoner/pattern_detection/detectors/confidence_calibration/analyzer.py
"""ConfidenceCalibrationAnalyzer — analyzes the ReasoningHistory confidence track (M2-7K, DET-10).

Responsibility: Single O(h) pass over ReasoningHistory entries.
Evaluates the QUALITY OF THE REASONING PIPELINE — not the candidate.
Produces CalibrationMetrics (immutable).

Computed fields:
  - confidence_history: list of reasoning_confidence values in order
  - confidence_variance: population variance of the confidence track
  - confidence_slope: mean of consecutive differences (proxy for trend)
  - confidence_oscillation: mean absolute change between consecutive values
  - confidence_saturation: fraction of entries at extreme values (0.0 or 1.0)
  - stability_score: 1.0 - oscillation (higher = more stable)
  - confidence_trend: "RISING" | "FALLING" | "STABLE" | "OSCILLATING" | "INSUFFICIENT"

Guard condition: returns zeroed metrics if history_length < MIN_HISTORY_LENGTH.

Future V1.2: CalibrationMetrics → CalibrationObservation(Observation).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.contracts.reasoning.reasoning_history import ReasoningEntry

MIN_HISTORY_LENGTH: int = 3
SATURATION_THRESHOLD: float = 0.05  # within 5% of 0.0 or 1.0 considered saturated


@dataclass(frozen=True)
class CalibrationMetrics:
    """Immutable snapshot of confidence track statistics.

    Future V1.2: promoted to CalibrationObservation with description field.
    """

    confidence_history: tuple[float, ...] = field(default_factory=tuple)
    confidence_variance: float = 0.0
    confidence_slope: float = 0.0       # positive = rising, negative = falling
    confidence_oscillation: float = 0.0 # mean absolute change
    confidence_saturation: float = 0.0  # fraction of entries at extremes
    stability_score: float = 1.0        # 1.0 - oscillation (clamped [0.0, 1.0])
    history_length: int = 0

    @property
    def confidence_trend(self) -> str:
        """RISING | FALLING | STABLE | OSCILLATING | INSUFFICIENT."""
        if self.history_length < MIN_HISTORY_LENGTH:
            return "INSUFFICIENT"
        if self.confidence_oscillation > 0.3:
            return "OSCILLATING"
        if self.confidence_slope > 0.05:
            return "RISING"
        if self.confidence_slope < -0.05:
            return "FALLING"
        return "STABLE"

    @property
    def mean_confidence(self) -> float:
        if not self.confidence_history:
            return 0.0
        return sum(self.confidence_history) / len(self.confidence_history)


class ConfidenceCalibrationAnalyzer:
    """Computes CalibrationMetrics from ReasoningHistory entries.

    Single O(h) pass; no external dependencies.
    """

    def analyze(self, entries: list[ReasoningEntry]) -> CalibrationMetrics:
        """Return CalibrationMetrics from confidence values in history entries."""
        n = len(entries)
        if n < MIN_HISTORY_LENGTH:
            return CalibrationMetrics(
                confidence_history=tuple(e.reasoning_confidence for e in entries),
                history_length=n,
            )

        values = [e.reasoning_confidence for e in entries]
        history_tuple = tuple(values)

        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n

        diffs = [values[i + 1] - values[i] for i in range(n - 1)]
        slope = sum(diffs) / len(diffs)
        oscillation = sum(abs(d) for d in diffs) / len(diffs)

        saturated = sum(
            1 for v in values
            if v <= SATURATION_THRESHOLD or v >= (1.0 - SATURATION_THRESHOLD)
        )
        saturation = saturated / n
        stability = max(0.0, min(1.0, 1.0 - oscillation))

        return CalibrationMetrics(
            confidence_history=history_tuple,
            confidence_variance=round(variance, 4),
            confidence_slope=round(slope, 4),
            confidence_oscillation=round(oscillation, 4),
            confidence_saturation=round(saturation, 4),
            stability_score=round(stability, 4),
            history_length=n,
        )
