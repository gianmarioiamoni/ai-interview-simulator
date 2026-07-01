# services/interview_reasoner/pattern_detection/detectors/leadership/analyzer.py
"""LeadershipAnalyzer — classifies EvidenceStore signals for leadership dimension (M2-7H, DET-11).

Responsibility: Single O(n) pass over behavioral EvidenceStore signals.
Classifies each signal as contributing to one or more leadership sub-dimensions:
  - Ownership:     BEHAVIORAL_GROWTH on PROBLEM_SOLVING with strong positive polarity
  - Initiative:    BEHAVIORAL_GROWTH signals with cross-area spread (multi-area)
  - Accountability: BEHAVIORAL_GROWTH following a BEHAVIORAL_INSTABILITY (recovery pattern)
  - Mentoring:     CROSS_AREA_CONSISTENT signals showing cross-area positive spread
  - Strategic:     CROSS_AREA_CONSISTENT across >= 3 distinct question areas

Input signals consumed (behavioral tier only):
  BEHAVIORAL_GROWTH, BEHAVIORAL_INSTABILITY, CROSS_AREA_CONSISTENT, CROSS_AREA_CONTRADICTORY

Per ADR-063: dimension anchor is ProfileDimension.PROBLEM_SOLVING (V1.1 temporary mapping).

Future V1.2: LeadershipStats → LeadershipObservation(Observation) with description field.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_type import EvidenceType

# Behavioral signals consumed by leadership analysis.
_BEHAVIORAL_GROWTH = EvidenceType.BEHAVIORAL_GROWTH
_BEHAVIORAL_INSTABILITY = EvidenceType.BEHAVIORAL_INSTABILITY
_CROSS_AREA_CONSISTENT = EvidenceType.CROSS_AREA_CONSISTENT
_CROSS_AREA_CONTRADICTORY = EvidenceType.CROSS_AREA_CONTRADICTORY

# Minimum distinct areas required to classify a strategic signal.
MIN_AREAS_FOR_STRATEGIC = 3

# Minimum behavioral signals before any analysis is performed.
MIN_BEHAVIORAL_SIGNALS = 2


@dataclass(frozen=True)
class LeadershipStats:
    """Leadership signal statistics derived from EvidenceStore.

    Future V1.2: will be promoted to LeadershipObservation with description field.
    """

    ownership_signal_count: int = 0       # BEHAVIORAL_GROWTH on PROBLEM_SOLVING, POSITIVE
    initiative_signal_count: int = 0      # BEHAVIORAL_GROWTH with multi-area spread
    accountability_signal_count: int = 0  # BEHAVIORAL_GROWTH following BEHAVIORAL_INSTABILITY
    mentoring_signal_count: int = 0       # CROSS_AREA_CONSISTENT positive spread patterns
    strategic_signal_count: int = 0       # CROSS_AREA_CONSISTENT across >= 3 distinct areas
    total_behavioral_signals: int = 0     # denominator for ratios

    @property
    def leadership_score(self) -> int:
        """Sum of all positive leadership sub-dimension signals."""
        return (
            self.ownership_signal_count
            + self.initiative_signal_count
            + self.accountability_signal_count
            + self.mentoring_signal_count
            + self.strategic_signal_count
        )

    @property
    def leadership_ratio(self) -> float:
        """(ownership + initiative + accountability) / total_behavioral_signals.

        Returns 0.0 when total == 0.
        """
        if self.total_behavioral_signals == 0:
            return 0.0
        numerator = (
            self.ownership_signal_count
            + self.initiative_signal_count
            + self.accountability_signal_count
        )
        return numerator / self.total_behavioral_signals

    @property
    def active_dimension_count(self) -> int:
        """Number of leadership sub-dimensions with at least one signal."""
        return sum([
            self.ownership_signal_count > 0,
            self.initiative_signal_count > 0,
            self.accountability_signal_count > 0,
            self.mentoring_signal_count > 0,
            self.strategic_signal_count > 0,
        ])

    @property
    def trend(self) -> str:
        """Coarse trend label based on ownership + initiative combined.

        RISING | STABLE | DECLINING | INSUFFICIENT
        """
        if self.total_behavioral_signals < MIN_BEHAVIORAL_SIGNALS:
            return "INSUFFICIENT"
        ownership_plus_initiative = self.ownership_signal_count + self.initiative_signal_count
        ratio = (
            ownership_plus_initiative / self.total_behavioral_signals
            if self.total_behavioral_signals > 0
            else 0.0
        )
        if ratio >= 0.5:
            return "RISING"
        if ratio >= 0.25:
            return "STABLE"
        return "DECLINING"


class LeadershipAnalyzer:
    """Classifies EvidenceStore behavioral signals for leadership dimensions.

    Single O(n) pass over the full EvidenceStore.
    Only signals from the behavioral family are consumed.
    """

    def analyze(self, signals: list[EvidenceSignal]) -> LeadershipStats:
        """Return LeadershipStats from behavioral signals in the EvidenceStore."""
        from domain.contracts.reasoning.profile_dimension import ProfileDimension

        behavioral_signals = [
            s for s in signals
            if s.signal_type in (
                _BEHAVIORAL_GROWTH,
                _BEHAVIORAL_INSTABILITY,
                _CROSS_AREA_CONSISTENT,
                _CROSS_AREA_CONTRADICTORY,
            )
        ]

        total = len(behavioral_signals)

        if total < MIN_BEHAVIORAL_SIGNALS:
            return LeadershipStats(total_behavioral_signals=total)

        ownership = 0
        initiative = 0
        accountability = 0
        mentoring = 0
        strategic = 0

        # Collect GROWTH and INSTABILITY signals separately for recovery detection.
        growth_indices: list[int] = []
        instability_indices: list[int] = []

        # Track question areas that have BEHAVIORAL_GROWTH (for initiative detection).
        growth_areas: set[str] = set()

        # Track distinct areas covered by CROSS_AREA_CONSISTENT (for strategic).
        consistent_areas: set[str] = set()

        for i, sig in enumerate(behavioral_signals):
            if sig.signal_type == _BEHAVIORAL_GROWTH and sig.polarity == EvidencePolarity.POSITIVE:
                # Ownership: BEHAVIORAL_GROWTH on PROBLEM_SOLVING
                if sig.dimension == ProfileDimension.PROBLEM_SOLVING:
                    ownership += 1
                # Initiative: track unique areas with BEHAVIORAL_GROWTH
                growth_areas.add(sig.question_area)
                growth_indices.append(i)

            elif sig.signal_type == _BEHAVIORAL_INSTABILITY:
                instability_indices.append(i)

            elif sig.signal_type == _CROSS_AREA_CONSISTENT and sig.polarity == EvidencePolarity.POSITIVE:
                consistent_areas.add(sig.question_area)
                mentoring += 1

        # Initiative: BEHAVIORAL_GROWTH present across multiple distinct areas.
        if len(growth_areas) >= 2:
            initiative = len(growth_areas) - 1

        # Accountability: recovery patterns — GROWTH following INSTABILITY.
        accountability = self._count_recoveries(
            growth_indices=growth_indices,
            instability_indices=instability_indices,
        )

        # Strategic: CROSS_AREA_CONSISTENT patterns across >= 3 distinct areas.
        if len(consistent_areas) >= MIN_AREAS_FOR_STRATEGIC:
            strategic = 1

        return LeadershipStats(
            ownership_signal_count=ownership,
            initiative_signal_count=initiative,
            accountability_signal_count=accountability,
            mentoring_signal_count=mentoring,
            strategic_signal_count=strategic,
            total_behavioral_signals=total,
        )

    def _count_recoveries(
        self,
        growth_indices: list[int],
        instability_indices: list[int],
    ) -> int:
        """Count recovery patterns: GROWTH signal after an INSTABILITY signal.

        A recovery is when any growth index j > any instability index i.
        O(n) via sets.
        """
        if not growth_indices or not instability_indices:
            return 0
        max_instability = max(instability_indices)
        recoveries = sum(1 for j in growth_indices if j > max_instability)
        return min(recoveries, len(instability_indices))
