# services/interview_reasoner/pattern_detection/detectors/reasoning_depth/scorer.py
"""ReasoningDepthScorer — classifies depth stats into verdict labels (M2-7B).

Responsibility: apply thresholds to DimensionDepthStats and produce a
per-dimension verdict string consumed by SignalFactory and the main detector.

Thresholds (from TDS §18.2, DET-05):
  HIGH  : depth_ratio ≥ HIGH_THRESHOLD  AND total ≥ MIN_EVIDENCE
  LOW   : depth_ratio ≤ LOW_THRESHOLD   AND total ≥ MIN_EVIDENCE
  otherwise: NEUTRAL (no signal emitted)

Trend verdict (session-scoped, requires ≥ TREND_WINDOW consecutive depth entries):
  IMPROVING   : last TREND_WINDOW cycles all have depth_ratio increasing
  STAGNATING  : last TREND_WINDOW cycles all have LOW verdict
  otherwise   : NEUTRAL
"""

from __future__ import annotations

from enum import Enum

from services.interview_reasoner.pattern_detection.detectors.reasoning_depth.analyzer import (
    DimensionDepthStats,
)

HIGH_THRESHOLD = 0.60
LOW_THRESHOLD = 0.30
MIN_EVIDENCE = 3         # minimum total signals to emit a verdict
TREND_WINDOW = 3         # consecutive cycles needed for trend verdict


class DepthVerdict(str, Enum):
    HIGH = "high"
    LOW = "low"
    NEUTRAL = "neutral"
    IMPROVING = "improving"


class ReasoningDepthScorer:
    """Converts DimensionDepthStats into DepthVerdict."""

    def score(self, stats: DimensionDepthStats) -> DepthVerdict:
        if stats.total < MIN_EVIDENCE:
            return DepthVerdict.NEUTRAL
        if stats.depth_ratio >= HIGH_THRESHOLD:
            return DepthVerdict.HIGH
        if stats.depth_ratio <= LOW_THRESHOLD:
            return DepthVerdict.LOW
        return DepthVerdict.NEUTRAL

    def trend_verdict(
        self,
        history_ratios: list[float],
    ) -> DepthVerdict:
        """Classify trend from a per-cycle depth_ratio history (most recent last).

        IMPROVING  : monotonically increasing over last TREND_WINDOW entries
        STAGNATING : all last TREND_WINDOW entries ≤ LOW_THRESHOLD
        NEUTRAL    : otherwise
        """
        if len(history_ratios) < TREND_WINDOW:
            return DepthVerdict.NEUTRAL
        recent = history_ratios[-TREND_WINDOW:]
        if all(recent[i] < recent[i + 1] for i in range(TREND_WINDOW - 1)):
            return DepthVerdict.IMPROVING
        if all(r <= LOW_THRESHOLD for r in recent):
            return DepthVerdict.LOW  # maps to STAGNATING
        return DepthVerdict.NEUTRAL
