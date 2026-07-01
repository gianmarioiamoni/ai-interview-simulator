# services/interview_reasoner/pattern_detection/detectors/adaptability/analyzer.py
"""AdaptabilityAnalyzer — classifies EvidenceStore signals for adaptability dimension (M2-7J, DET-13).

Recovery detection follows ADR-065:
  - INSTABILITY event at question index `i` is "recovered" if a BEHAVIORAL_GROWTH signal
    appears within questions i+1 to i+3 (same or adjacent dimension).
  - Window size RECOVERY_WINDOW_QUESTIONS = 3 (module-level constant).
  - Unmatched INSTABILITY events after the window count as rigidity_count.

Input signals consumed (read-only from behavioral tier):
  BEHAVIORAL_GROWTH, BEHAVIORAL_INSTABILITY, CROSS_AREA_CONSISTENT, CROSS_AREA_CONTRADICTORY

Per V1.1 mapping: no dedicated ADAPTABILITY dimension; uses PROBLEM_SOLVING as proxy.

Future V1.2: AdaptabilityStats → AdaptabilityObservation(Observation) with description field.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_type import EvidenceType

# ADR-065: recovery window size in question indices.
RECOVERY_WINDOW_QUESTIONS: int = 3

# Behavioral signal types this analyzer consumes.
_CONSUMED_TYPES: frozenset[EvidenceType] = frozenset({
    EvidenceType.BEHAVIORAL_GROWTH,
    EvidenceType.BEHAVIORAL_INSTABILITY,
    EvidenceType.CROSS_AREA_CONSISTENT,
    EvidenceType.CROSS_AREA_CONTRADICTORY,
})

# Minimum behavioral signals before analysis proceeds.
MIN_BEHAVIORAL_SIGNALS: int = 2


@dataclass(frozen=True)
class AdaptabilityStats:
    """Adaptability signal statistics derived from EvidenceStore.

    Future V1.2: promoted to AdaptabilityObservation with description field.
    """

    recovery_count: int = 0             # INSTABILITY -> GROWTH sequences within window
    rigidity_count: int = 0             # INSTABILITY events with no recovery within window
    flexibility_count: int = 0          # CROSS_AREA_CONSISTENT signals with positive polarity
    context_switch_count: int = 0       # distinct area transitions with consistent performance
    reframing_events: int = 0           # CROSS_AREA_CONTRADICTORY (potential reframing)
    total_instability_events: int = 0
    total_behavioral_signals: int = 0

    @property
    def adaptability_ratio(self) -> float:
        """recovery_count / max(1, total_instability_events)."""
        return self.recovery_count / max(1, self.total_instability_events)

    @property
    def flexibility_ratio(self) -> float:
        """flexibility_count / max(1, context_switch_count)."""
        return self.flexibility_count / max(1, self.context_switch_count)

    @property
    def trend(self) -> str:
        """IMPROVING | STABLE | DECLINING | INSUFFICIENT."""
        if self.total_instability_events < MIN_BEHAVIORAL_SIGNALS:
            if self.flexibility_count < 3:
                return "INSUFFICIENT"
        if self.recovery_count >= self.rigidity_count and self.recovery_count > 0:
            if self.flexibility_count > 0:
                return "IMPROVING"
            return "STABLE"
        if self.rigidity_count > self.recovery_count:
            return "DECLINING"
        return "STABLE"


class AdaptabilityAnalyzer:
    """Classifies EvidenceStore behavioral signals for adaptability dimensions.

    Single O(n) pass over the full EvidenceStore.
    Recovery detection follows ADR-065 (window-based INSTABILITY → GROWTH matching).
    """

    def analyze(self, signals: list[EvidenceSignal]) -> AdaptabilityStats:
        """Return AdaptabilityStats from behavioral signals in the EvidenceStore."""
        behavioral_signals = [s for s in signals if s.signal_type in _CONSUMED_TYPES]
        total = len(behavioral_signals)

        if total < MIN_BEHAVIORAL_SIGNALS:
            return AdaptabilityStats(total_behavioral_signals=total)

        instability_events: list[tuple[int, str]] = []  # (question_index, dimension_or_area)
        growth_events: list[tuple[int, str]] = []       # (question_index, dimension_or_area)
        flexibility = 0
        distinct_areas: set[str] = set()
        reframing = 0

        for sig in behavioral_signals:
            st = sig.signal_type
            q_idx = sig.question_index
            area = sig.question_area

            if st == EvidenceType.BEHAVIORAL_INSTABILITY:
                instability_events.append((q_idx, area))

            elif st == EvidenceType.BEHAVIORAL_GROWTH and sig.polarity == EvidencePolarity.POSITIVE:
                growth_events.append((q_idx, area))

            elif st == EvidenceType.CROSS_AREA_CONSISTENT and sig.polarity == EvidencePolarity.POSITIVE:
                flexibility += 1
                distinct_areas.add(area)

            elif st == EvidenceType.CROSS_AREA_CONTRADICTORY:
                reframing += 1

        recovery_count, rigidity_count = self._match_recoveries(
            instability_events=instability_events,
            growth_events=growth_events,
        )

        return AdaptabilityStats(
            recovery_count=recovery_count,
            rigidity_count=rigidity_count,
            flexibility_count=flexibility,
            context_switch_count=len(distinct_areas),
            reframing_events=reframing,
            total_instability_events=len(instability_events),
            total_behavioral_signals=total,
        )

    def _match_recoveries(
        self,
        instability_events: list[tuple[int, str]],
        growth_events: list[tuple[int, str]],
    ) -> tuple[int, int]:
        """Match each INSTABILITY to a GROWTH within the recovery window (ADR-065).

        Algorithm:
          - Single forward pass over instability events.
          - For each instability at index i, search growth events where j in [i+1, i+3].
          - Adjacent dimension: same question_area OR growth in any area (relaxed V1.1 rule).
          - Each growth event can only recover one instability (first-come first-served).
          - Unmatched instability events → rigidity_count.

        Returns (recovery_count, rigidity_count). O(n) via set tracking.
        """
        used_growth: set[int] = set()  # indices into growth_events list
        recovery = 0
        rigidity = 0

        for inst_q, inst_area in instability_events:
            matched = False
            for gidx, (grow_q, grow_area) in enumerate(growth_events):
                if gidx in used_growth:
                    continue
                if inst_q < grow_q <= inst_q + RECOVERY_WINDOW_QUESTIONS:
                    # Adjacent: same area OR any area (V1.1 relaxed rule)
                    used_growth.add(gidx)
                    recovery += 1
                    matched = True
                    break
            if not matched:
                rigidity += 1

        return recovery, rigidity
