# services/interview_reasoner/pattern_detection/detectors/collaboration/scorer.py
"""CollaborationScorer — threshold verdicts for collaboration stats (M2-7I, DET-12).

Thresholds (TDS §20.3.5):
  STRONG_COLLABORATOR    : collaboration_ratio >= 0.55 AND conflict_resolution_ratio >= 0.60
  EFFECTIVE_COLLABORATOR : collaboration_ratio >= 0.30 OR cross_functional_count >= 2
  COLLABORATION_DEFICIT  : total >= MIN but collaboration indicators absent/minimal
  NEUTRAL                : guard conditions not met (total < MIN_BEHAVIORAL_SIGNALS)

Verdict precedence: STRONG_COLLABORATOR > EFFECTIVE_COLLABORATOR > COLLABORATION_DEFICIT > NEUTRAL.
Deterministic; no randomness; no heuristics outside frozen TDS.
"""

from __future__ import annotations

from enum import Enum

from services.interview_reasoner.pattern_detection.detectors.collaboration.analyzer import (
    CollaborationStats,
)

MIN_BEHAVIORAL_SIGNALS         = 3
MIN_COLLAB_RATIO_STRONG        = 0.55
MIN_COLLAB_RATIO_EFFECTIVE     = 0.30
MIN_CONFLICT_RESOLUTION_STRONG = 0.60
MIN_CROSS_FUNCTIONAL_EFFECTIVE = 2


class CollaborationVerdict(str, Enum):
    STRONG_COLLABORATOR    = "STRONG_COLLABORATOR"
    EFFECTIVE_COLLABORATOR = "EFFECTIVE_COLLABORATOR"
    NEUTRAL                = "NEUTRAL"
    COLLABORATION_DEFICIT  = "COLLABORATION_DEFICIT"


class CollaborationScorer:
    """Converts CollaborationStats into CollaborationVerdict. Pure deterministic function."""

    def score(self, stats: CollaborationStats) -> CollaborationVerdict:
        """Return verdict; NEUTRAL when guard conditions are not met."""
        if stats.total_behavioral_signals < MIN_BEHAVIORAL_SIGNALS:
            return CollaborationVerdict.NEUTRAL

        ratio = stats.collaboration_ratio
        conflict_res = stats.conflict_resolution_ratio
        cross_func = stats.cross_functional_count

        if ratio >= MIN_COLLAB_RATIO_STRONG and conflict_res >= MIN_CONFLICT_RESOLUTION_STRONG:
            return CollaborationVerdict.STRONG_COLLABORATOR

        if ratio >= MIN_COLLAB_RATIO_EFFECTIVE or cross_func >= MIN_CROSS_FUNCTIONAL_EFFECTIVE:
            return CollaborationVerdict.EFFECTIVE_COLLABORATOR

        collab_score = (
            stats.team_orientation_count
            + stats.knowledge_sharing_count
            + stats.feedback_acceptance_count
        )
        if collab_score == 0:
            return CollaborationVerdict.COLLABORATION_DEFICIT

        return CollaborationVerdict.NEUTRAL
