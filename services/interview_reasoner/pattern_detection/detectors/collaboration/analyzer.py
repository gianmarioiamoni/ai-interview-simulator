# services/interview_reasoner/pattern_detection/detectors/collaboration/analyzer.py
"""CollaborationAnalyzer — classifies EvidenceStore signals for collaboration dimension (M2-7I, DET-12).

Responsibility: Single O(n) pass over behavioral EvidenceStore signals. Classifies each
signal as contributing to one or more collaboration sub-dimensions:
  - Team orientation:      BEHAVIORAL_GROWTH on COMMUNICATION dim (team-first framing)
  - Knowledge sharing:     CROSS_AREA_CONSISTENT positive signals (enabling others cross-area)
  - Conflict signals:      BEHAVIORAL_INSTABILITY (negative) and BEHAVIORAL_GROWTH following it (positive)
  - Feedback acceptance:   BEHAVIORAL_GROWTH after BEHAVIORAL_INSTABILITY (recovery = accepting correction)
  - Cross-functional:      CROSS_AREA_CONSISTENT spanning >= 2 distinct question areas

Input signals consumed (behavioral tier only):
  BEHAVIORAL_GROWTH, BEHAVIORAL_INSTABILITY, CROSS_AREA_CONSISTENT, CROSS_AREA_CONTRADICTORY,
  LEADERSHIP_EMERGING, LEADERSHIP_STRONG (read-only; used only to enrich team_orientation count)

Per ADR-064: dimension anchor is ProfileDimension.COMMUNICATION (V1.1 temporary mapping).

Future V1.2: CollaborationStats → CollaborationObservation(Observation) with description field.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_type import EvidenceType

# Behavioral + leadership signals consumed by collaboration analysis.
_CONSUMED_TYPES: frozenset[EvidenceType] = frozenset({
    EvidenceType.BEHAVIORAL_GROWTH,
    EvidenceType.BEHAVIORAL_INSTABILITY,
    EvidenceType.CROSS_AREA_CONSISTENT,
    EvidenceType.CROSS_AREA_CONTRADICTORY,
    EvidenceType.LEADERSHIP_EMERGING,
    EvidenceType.LEADERSHIP_STRONG,
})

# Minimum distinct areas for cross-functional signal.
MIN_AREAS_FOR_CROSS_FUNCTIONAL = 2

# Minimum behavioral signals before analysis proceeds.
MIN_BEHAVIORAL_SIGNALS = 2


@dataclass(frozen=True)
class CollaborationStats:
    """Collaboration signal statistics derived from EvidenceStore.

    Future V1.2: promoted to CollaborationObservation with description field.
    """

    team_orientation_count: int = 0       # BEHAVIORAL_GROWTH on COMMUNICATION + co-leadership signals
    knowledge_sharing_count: int = 0      # CROSS_AREA_CONSISTENT positive signals
    conflict_signals_count: int = 0       # total conflict-related signals
    positive_conflict_count: int = 0      # conflict managed well (recovery patterns)
    feedback_acceptance_count: int = 0    # BEHAVIORAL_GROWTH after BEHAVIORAL_INSTABILITY
    cross_functional_count: int = 0       # distinct areas covered by CROSS_AREA_CONSISTENT
    total_behavioral_signals: int = 0     # denominator

    @property
    def collaboration_ratio(self) -> float:
        """(team_orientation + knowledge_sharing + feedback_acceptance) / total_behavioral_signals."""
        if self.total_behavioral_signals == 0:
            return 0.0
        numerator = (
            self.team_orientation_count
            + self.knowledge_sharing_count
            + self.feedback_acceptance_count
        )
        return numerator / self.total_behavioral_signals

    @property
    def conflict_resolution_ratio(self) -> float:
        """positive_conflict / conflict_signals_count; returns 1.0 if no conflict signals."""
        if self.conflict_signals_count == 0:
            return 1.0
        return self.positive_conflict_count / self.conflict_signals_count

    @property
    def trend(self) -> str:
        """Coarse trend label.

        RISING | STABLE | DECLINING | INSUFFICIENT
        """
        if self.total_behavioral_signals < MIN_BEHAVIORAL_SIGNALS:
            return "INSUFFICIENT"
        collab_score = self.team_orientation_count + self.knowledge_sharing_count
        ratio = (
            collab_score / self.total_behavioral_signals
            if self.total_behavioral_signals > 0
            else 0.0
        )
        if ratio >= 0.5:
            return "RISING"
        if ratio >= 0.2:
            return "STABLE"
        return "DECLINING"


class CollaborationAnalyzer:
    """Classifies EvidenceStore behavioral signals for collaboration dimensions.

    Single O(n) pass over the full EvidenceStore.
    Reads LEADERSHIP_* signals to enrich team_orientation (read-only).
    Never rewrites or modifies leadership signals.
    """

    def analyze(self, signals: list[EvidenceSignal]) -> CollaborationStats:
        """Return CollaborationStats from behavioral signals in the EvidenceStore."""
        from domain.contracts.reasoning.profile_dimension import ProfileDimension

        behavioral_signals = [s for s in signals if s.signal_type in _CONSUMED_TYPES]
        total = len(behavioral_signals)

        if total < MIN_BEHAVIORAL_SIGNALS:
            return CollaborationStats(total_behavioral_signals=total)

        team_orientation = 0
        knowledge_sharing = 0
        conflict_total = 0
        conflict_positive = 0
        feedback_acceptance = 0

        # Distinct areas covered by CROSS_AREA_CONSISTENT (for cross-functional).
        consistent_areas: set[str] = set()

        # Track INSTABILITY and GROWTH indices for feedback acceptance (recovery).
        instability_indices: list[int] = []
        growth_indices: list[int] = []

        for i, sig in enumerate(behavioral_signals):
            st = sig.signal_type

            if st == EvidenceType.BEHAVIORAL_GROWTH and sig.polarity == EvidencePolarity.POSITIVE:
                # Team orientation: BEHAVIORAL_GROWTH on COMMUNICATION dimension.
                if sig.dimension == ProfileDimension.COMMUNICATION:
                    team_orientation += 1
                growth_indices.append(i)

            elif st == EvidenceType.BEHAVIORAL_INSTABILITY:
                conflict_total += 1
                instability_indices.append(i)

            elif st == EvidenceType.CROSS_AREA_CONSISTENT and sig.polarity == EvidencePolarity.POSITIVE:
                knowledge_sharing += 1
                consistent_areas.add(sig.question_area)

            elif st in (EvidenceType.LEADERSHIP_EMERGING, EvidenceType.LEADERSHIP_STRONG):
                if sig.polarity == EvidencePolarity.POSITIVE:
                    team_orientation += 1

        # Feedback acceptance: GROWTH signals that appear after at least one INSTABILITY.
        feedback_acceptance = self._count_recoveries(
            growth_indices=growth_indices,
            instability_indices=instability_indices,
        )

        # Conflict managed = recovery patterns.
        conflict_positive = feedback_acceptance

        cross_functional = len(consistent_areas)

        return CollaborationStats(
            team_orientation_count=team_orientation,
            knowledge_sharing_count=knowledge_sharing,
            conflict_signals_count=conflict_total,
            positive_conflict_count=conflict_positive,
            feedback_acceptance_count=feedback_acceptance,
            cross_functional_count=cross_functional,
            total_behavioral_signals=total,
        )

    def _count_recoveries(
        self,
        growth_indices: list[int],
        instability_indices: list[int],
    ) -> int:
        """Count recovery patterns: GROWTH signal appearing after an INSTABILITY signal.

        O(n) via set lookup.
        """
        if not growth_indices or not instability_indices:
            return 0
        max_instability = max(instability_indices)
        recoveries = sum(1 for j in growth_indices if j > max_instability)
        return min(recoveries, len(instability_indices))
