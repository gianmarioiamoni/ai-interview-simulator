# services/interview_reasoner/pattern_detection/detectors/reasoning_depth/analyzer.py
"""ReasoningDepthAnalyzer — evidence classification and depth-ratio computation (M2-7B).

Responsibility: group EvidenceStore signals into depth-relevant categories and
compute per-dimension depth ratios.

Depth ratio per dimension:
    ratio = depth_count / (depth_count + shallow_count)
    where:
      depth_count  = signals with type in DEEP_TYPES and POSITIVE polarity
      shallow_count = signals with type in SHALLOW_TYPES and NEGATIVE polarity

O(n) single pass over new signals only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension

# Signal types that indicate deep reasoning (positive evidence of depth).
DEEP_TYPES: frozenset[EvidenceType] = frozenset({
    EvidenceType.DEMONSTRATED_DEPTH,
    EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED,
    EvidenceType.REPEATED_STRENGTH,
    EvidenceType.RECOVERED_WEAKNESS,
})

# Signal types that indicate shallow reasoning (negative evidence of depth).
SHALLOW_TYPES: frozenset[EvidenceType] = frozenset({
    EvidenceType.REASONING_GAP,
    EvidenceType.SHALLOW_ANSWER,
    EvidenceType.KNOWLEDGE_GAP,
})


@dataclass(frozen=True)
class DimensionDepthStats:
    """Depth statistics for a single ProfileDimension."""

    dimension: ProfileDimension
    depth_count: int = 0
    shallow_count: int = 0

    @property
    def total(self) -> int:
        return self.depth_count + self.shallow_count

    @property
    def depth_ratio(self) -> float:
        """Returns [0.0, 1.0]; 0.5 when total == 0 (neutral)."""
        if self.total == 0:
            return 0.5
        return self.depth_count / self.total


class ReasoningDepthAnalyzer:
    """Classifies EvidenceSignals into depth vs. shallow categories per dimension.

    Operates on the full EvidenceStore (not just new signals) so that the
    depth ratio reflects the accumulated session evidence.  Still O(n).
    """

    def analyze(
        self,
        signals: list[EvidenceSignal],
    ) -> dict[ProfileDimension, DimensionDepthStats]:
        """Return per-dimension DimensionDepthStats.

        Single O(n) pass.
        """
        acc: dict[ProfileDimension, list[int]] = {}  # [depth_count, shallow_count]

        for sig in signals:
            if sig.dimension not in acc:
                acc[sig.dimension] = [0, 0]

            if sig.signal_type in DEEP_TYPES and sig.polarity == EvidencePolarity.POSITIVE:
                acc[sig.dimension][0] += 1
            elif sig.signal_type in SHALLOW_TYPES and sig.polarity == EvidencePolarity.NEGATIVE:
                acc[sig.dimension][1] += 1

        return {
            dim: DimensionDepthStats(dimension=dim, depth_count=counts[0], shallow_count=counts[1])
            for dim, counts in acc.items()
        }
