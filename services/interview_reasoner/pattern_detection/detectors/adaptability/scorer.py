# services/interview_reasoner/pattern_detection/detectors/adaptability/scorer.py
"""AdaptabilityScorer — threshold verdicts for adaptability stats (M2-7J, DET-13).

Thresholds (TDS §20.4.5):
  HIGHLY_ADAPTABLE : adaptability_ratio >= 0.70 AND trend != "DECLINING"
  ADAPTABLE        : ratio >= 0.40 OR flexibility_ratio >= 0.50
                     OR (total_instability == 0 AND flexibility_count >= 3)
  LOW_ADAPTABILITY : rigidity_count > recovery_count AND rigidity_count >= 2
  NEUTRAL          : guard conditions not met

Guard condition: Returns NEUTRAL if total_instability_events < MIN_INSTABILITY_EVENTS
                 AND flexibility_count < 3.

Verdict precedence: HIGHLY_ADAPTABLE > ADAPTABLE > LOW_ADAPTABILITY > NEUTRAL.
Deterministic; no randomness; no heuristics outside frozen TDS.
"""

from __future__ import annotations

from enum import Enum

from services.interview_reasoner.pattern_detection.detectors.adaptability.analyzer import (
    AdaptabilityStats,
)

MIN_INSTABILITY_EVENTS           = 2
RECOVERY_WINDOW_QUESTIONS        = 3
MIN_ADAPTABILITY_RATIO_HIGH      = 0.70
MIN_ADAPTABILITY_RATIO_ADAPTABLE = 0.40
MIN_FLEXIBILITY_RATIO_ADAPTABLE  = 0.50
LOW_ADAPTABILITY_RIGIDITY_FLOOR  = 2


class AdaptabilityVerdict(str, Enum):
    HIGHLY_ADAPTABLE = "HIGHLY_ADAPTABLE"
    ADAPTABLE        = "ADAPTABLE"
    NEUTRAL          = "NEUTRAL"
    LOW_ADAPTABILITY = "LOW_ADAPTABILITY"


class AdaptabilityScorer:
    """Converts AdaptabilityStats into AdaptabilityVerdict. Pure deterministic function."""

    def score(self, stats: AdaptabilityStats) -> AdaptabilityVerdict:
        """Return verdict. NEUTRAL when guard conditions are not met."""
        # Guard: insufficient data
        if (
            stats.total_instability_events < MIN_INSTABILITY_EVENTS
            and stats.flexibility_count < 3
        ):
            return AdaptabilityVerdict.NEUTRAL

        # Special rule: proactive flexibility (no instability, but flexible)
        if stats.total_instability_events == 0 and stats.flexibility_count >= 3:
            return AdaptabilityVerdict.ADAPTABLE

        ratio = stats.adaptability_ratio
        flex_ratio = stats.flexibility_ratio
        trend = stats.trend

        if ratio >= MIN_ADAPTABILITY_RATIO_HIGH and trend != "DECLINING":
            return AdaptabilityVerdict.HIGHLY_ADAPTABLE

        if ratio >= MIN_ADAPTABILITY_RATIO_ADAPTABLE or flex_ratio >= MIN_FLEXIBILITY_RATIO_ADAPTABLE:
            return AdaptabilityVerdict.ADAPTABLE

        if (
            stats.rigidity_count > stats.recovery_count
            and stats.rigidity_count >= LOW_ADAPTABILITY_RIGIDITY_FLOOR
        ):
            return AdaptabilityVerdict.LOW_ADAPTABILITY

        return AdaptabilityVerdict.NEUTRAL
