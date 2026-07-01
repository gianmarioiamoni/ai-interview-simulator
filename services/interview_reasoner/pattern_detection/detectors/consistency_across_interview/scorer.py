# services/interview_reasoner/pattern_detection/detectors/consistency_across_interview/scorer.py
"""ConsistencyScorer — converts CrossAreaResult into ConsistencyVerdict (M2-7D, DET-09).

Precedence:
  CONTRADICTORY → has_contradiction = True
  CONSISTENT    → has_consistency = True (and NOT contradictory)
  NEUTRAL       → insufficient data or ambiguous

Future V1.2: CrossDomainConsistencyFeature aggregates verdicts across all dimensions.
"""

from __future__ import annotations

from enum import Enum

from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview.analyzer import (
    CrossAreaResult,
)


class ConsistencyVerdict(str, Enum):
    CONTRADICTORY = "contradictory"
    CONSISTENT = "consistent"
    NEUTRAL = "neutral"


class ConsistencyScorer:
    """Converts CrossAreaResult into ConsistencyVerdict."""

    def score(self, result: CrossAreaResult) -> ConsistencyVerdict:
        if result.has_contradiction:
            return ConsistencyVerdict.CONTRADICTORY
        if result.has_consistency:
            return ConsistencyVerdict.CONSISTENT
        return ConsistencyVerdict.NEUTRAL
