# services/interview_reasoner/pattern_detection/detectors/consistency_across_interview/analyzer.py
"""ConsistencyHistoryAnalyzer — cross-area consistency analysis (M2-7D, DET-09).

Responsibility: Group EvidenceStore signals by (dimension, question_area) and
compute per-area polarity ratios. Then identify whether areas belonging to the
same dimension show contradictory or consistent polarity patterns.

Algorithm:
  1. Single O(n) pass: build area_stats[dim][area] = [pos_count, neg_count]
  2. For each dimension with ≥ 2 areas, compare polarity ratios
  3. Contradiction: |ratio_a - ratio_b| ≥ CONTRADICTION_THRESHOLD
  4. Consistent: all areas have similar polarity ratios

O(n) over signals; O(d × a) over dimensions × areas (typically small).

Future V1.2 Observation type: ConsistencyObservation
Future ProfileFeature: CrossDomainConsistencyFeature
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.profile_dimension import ProfileDimension

# Minimum signals per area to include it in cross-area comparison.
MIN_SIGNALS_PER_AREA = 2

# Threshold for calling a contradiction between two areas.
CONTRADICTION_THRESHOLD = 0.4

# Threshold for calling consistent cross-area performance.
CONSISTENCY_THRESHOLD = 0.25


@dataclass(frozen=True)
class AreaStats:
    """Polarity stats for a single (dimension, question_area) pair."""

    dimension: ProfileDimension
    area: str
    positive_count: int = 0
    negative_count: int = 0

    @property
    def total(self) -> int:
        return self.positive_count + self.negative_count

    @property
    def positive_ratio(self) -> float:
        if self.total == 0:
            return 0.5
        return self.positive_count / self.total


@dataclass(frozen=True)
class CrossAreaResult:
    """Result of cross-area comparison for a single dimension.

    Future V1.2: promoted to ConsistencyObservation with description field.
    """

    dimension: ProfileDimension
    has_contradiction: bool = False
    has_consistency: bool = False
    # Areas involved in the most significant contradiction (for label).
    contradictory_areas: tuple[str, str] = ("", "")
    # Max difference between any two area ratios.
    max_ratio_delta: float = 0.0


class ConsistencyHistoryAnalyzer:
    """Analyzes cross-area consistency from EvidenceStore signals.

    O(n) pass to build area maps; O(d × a²) for comparison (a is typically 2–5).
    """

    def analyze(self, signals: list[EvidenceSignal]) -> list[CrossAreaResult]:
        """Return CrossAreaResult per dimension where ≥ 2 areas exist."""
        # O(n) pass: build acc[dim][area] = [pos, neg]
        acc: dict[ProfileDimension, dict[str, list[int]]] = {}
        for sig in signals:
            dim = sig.dimension
            area = sig.question_area
            if dim not in acc:
                acc[dim] = {}
            if area not in acc[dim]:
                acc[dim][area] = [0, 0]
            if sig.polarity == EvidencePolarity.POSITIVE:
                acc[dim][area][0] += 1
            else:
                acc[dim][area][1] += 1

        results: list[CrossAreaResult] = []
        for dim, areas in acc.items():
            # Filter areas with enough signals.
            qualified = {
                a: AreaStats(
                    dimension=dim,
                    area=a,
                    positive_count=counts[0],
                    negative_count=counts[1],
                )
                for a, counts in areas.items()
                if counts[0] + counts[1] >= MIN_SIGNALS_PER_AREA
            }
            if len(qualified) < 2:
                continue

            result = self._compare_areas(dim, list(qualified.values()))
            results.append(result)

        return results

    def _compare_areas(
        self,
        dim: ProfileDimension,
        area_stats: list[AreaStats],
    ) -> CrossAreaResult:
        """Find the max ratio delta across all area pairs (O(a²), a typically ≤ 5)."""
        max_delta = 0.0
        worst_pair: tuple[str, str] = ("", "")

        for i in range(len(area_stats)):
            for j in range(i + 1, len(area_stats)):
                delta = abs(area_stats[i].positive_ratio - area_stats[j].positive_ratio)
                if delta > max_delta:
                    max_delta = delta
                    worst_pair = (area_stats[i].area, area_stats[j].area)

        has_contradiction = max_delta >= CONTRADICTION_THRESHOLD
        has_consistency = max_delta < CONSISTENCY_THRESHOLD

        return CrossAreaResult(
            dimension=dim,
            has_contradiction=has_contradiction,
            has_consistency=has_consistency,
            contradictory_areas=worst_pair,
            max_ratio_delta=round(max_delta, 4),
        )
