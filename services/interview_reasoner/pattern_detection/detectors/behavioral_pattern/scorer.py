# services/interview_reasoner/pattern_detection/detectors/behavioral_pattern/scorer.py
"""BehaviorPatternScorer — converts BehavioralStats into BehaviorVerdict (M2-7D).

Thresholds (TDS §18.2, DET-08):
  GROWTH      : has_growth = True
  INSTABILITY : has_instability = True AND NOT has_growth
  PLATEAU     : has_plateau = True AND NOT has_growth AND NOT has_instability
  NEUTRAL     : insufficient data or ambiguous

GROWTH takes precedence over PLATEAU and INSTABILITY.
INSTABILITY takes precedence over PLATEAU.

Future V1.2: BehavioralObservation will carry confidence derived from entry_count.
"""

from __future__ import annotations

from enum import Enum

from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern.analyzer import (
    BehavioralStats,
    MIN_ENTRIES,
)


class BehaviorVerdict(str, Enum):
    GROWTH = "growth"
    INSTABILITY = "instability"
    PLATEAU = "plateau"
    NEUTRAL = "neutral"


class BehaviorPatternScorer:
    """Converts BehavioralStats into BehaviorVerdict."""

    def score(self, stats: BehavioralStats) -> BehaviorVerdict:
        if stats.entry_count < MIN_ENTRIES:
            return BehaviorVerdict.NEUTRAL
        if stats.has_growth:
            return BehaviorVerdict.GROWTH
        if stats.has_instability:
            return BehaviorVerdict.INSTABILITY
        if stats.has_plateau:
            return BehaviorVerdict.PLATEAU
        return BehaviorVerdict.NEUTRAL
