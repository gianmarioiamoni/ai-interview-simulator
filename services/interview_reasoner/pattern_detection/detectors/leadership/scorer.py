# services/interview_reasoner/pattern_detection/detectors/leadership/scorer.py
"""LeadershipScorer — threshold verdicts for leadership stats (M2-7H, DET-11).

Thresholds (TDS §20.2.5):
  STRONG_LEADER     : leadership_ratio >= 0.60 AND active_dimension_count >= 2
  EMERGING_LEADER   : leadership_ratio >= 0.35 AND active_dimension_count >= 1
  LEADERSHIP_ABSENT : total_behavioral_signals >= MIN but no leadership-coded signals
  NEUTRAL           : guard conditions not met (total < MIN_BEHAVIORAL_SIGNALS)

Verdict precedence: STRONG_LEADER > EMERGING_LEADER > LEADERSHIP_ABSENT > NEUTRAL.
Deterministic; no randomness; no heuristics outside frozen TDS.
"""

from __future__ import annotations

from enum import Enum

from services.interview_reasoner.pattern_detection.detectors.leadership.analyzer import (
    LeadershipStats,
)

MIN_BEHAVIORAL_SIGNALS     = 3
MIN_LEADERSHIP_RATIO_STRONG    = 0.60
MIN_LEADERSHIP_RATIO_EMERGING  = 0.35
MIN_DIMENSIONS_STRONG          = 2
MIN_DIMENSIONS_EMERGING        = 1


class LeadershipVerdict(str, Enum):
    STRONG_LEADER     = "STRONG_LEADER"
    EMERGING_LEADER   = "EMERGING_LEADER"
    NEUTRAL           = "NEUTRAL"
    LEADERSHIP_ABSENT = "LEADERSHIP_ABSENT"


class LeadershipScorer:
    """Converts LeadershipStats into LeadershipVerdict. Pure deterministic function."""

    def score(self, stats: LeadershipStats) -> LeadershipVerdict:
        """Return verdict; NEUTRAL when guard conditions are not met."""
        if stats.total_behavioral_signals < MIN_BEHAVIORAL_SIGNALS:
            return LeadershipVerdict.NEUTRAL

        ratio = stats.leadership_ratio
        dims = stats.active_dimension_count

        if ratio >= MIN_LEADERSHIP_RATIO_STRONG and dims >= MIN_DIMENSIONS_STRONG:
            return LeadershipVerdict.STRONG_LEADER

        if ratio >= MIN_LEADERSHIP_RATIO_EMERGING and dims >= MIN_DIMENSIONS_EMERGING:
            return LeadershipVerdict.EMERGING_LEADER

        if stats.leadership_score == 0:
            return LeadershipVerdict.LEADERSHIP_ABSENT

        return LeadershipVerdict.NEUTRAL
