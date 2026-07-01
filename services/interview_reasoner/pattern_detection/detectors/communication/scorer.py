# services/interview_reasoner/pattern_detection/detectors/communication/scorer.py
"""CommunicationScorer — threshold verdicts for communication stats (M2-7C).

Thresholds (TDS §18.2, DET-07):
  CLEAR        : strength_ratio ≥ CLEAR_THRESHOLD AND total ≥ MIN_EVIDENCE
  WEAK         : strength_ratio ≤ WEAK_THRESHOLD  AND total ≥ MIN_EVIDENCE
  INCONSISTENT : has_inconsistency AND total ≥ MIN_EVIDENCE
  NEUTRAL      : otherwise

INCONSISTENT takes precedence over CLEAR/WEAK.
"""

from __future__ import annotations

from enum import Enum

from services.interview_reasoner.pattern_detection.detectors.communication.analyzer import (
    CommunicationStats,
)

CLEAR_THRESHOLD = 0.65
WEAK_THRESHOLD = 0.35
MIN_EVIDENCE = 2       # minimum COMMUNICATION signals to emit a verdict (TDS DET-07: ≥ 2)


class CommunicationVerdict(str, Enum):
    CLEAR = "clear"
    WEAK = "weak"
    INCONSISTENT = "inconsistent"
    NEUTRAL = "neutral"


class CommunicationScorer:
    """Converts CommunicationStats into CommunicationVerdict."""

    def score(self, stats: CommunicationStats) -> CommunicationVerdict:
        if stats.total < MIN_EVIDENCE:
            return CommunicationVerdict.NEUTRAL
        if stats.has_inconsistency:
            return CommunicationVerdict.INCONSISTENT
        if stats.strength_ratio >= CLEAR_THRESHOLD:
            return CommunicationVerdict.CLEAR
        if stats.strength_ratio <= WEAK_THRESHOLD:
            return CommunicationVerdict.WEAK
        return CommunicationVerdict.NEUTRAL
