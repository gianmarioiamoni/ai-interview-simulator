# services/interview_reasoner/pattern_detection/detectors/communication/analyzer.py
"""CommunicationObservationExtractor — classifies EvidenceStore signals for COMMUNICATION dimension (M2-7C).

Responsibility: Identify and group signals on the COMMUNICATION dimension.

Communication-positive signals (POSITIVE polarity):
  - REPEATED_STRENGTH on COMMUNICATION dim
  - DEMONSTRATED_DEPTH on COMMUNICATION dim

Communication-negative signals (NEGATIVE polarity):
  - COMMUNICATION_GAP
  - SHALLOW_ANSWER on COMMUNICATION dim

Communication-inconsistent signals:
  - CONTRADICTORY_ANSWER on COMMUNICATION dim

O(n) single pass.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension

# Positive communication signal types (require POSITIVE polarity).
COMM_POSITIVE_TYPES: frozenset[EvidenceType] = frozenset({
    EvidenceType.REPEATED_STRENGTH,
    EvidenceType.DEMONSTRATED_DEPTH,
})

# Negative communication signal types (require NEGATIVE polarity).
COMM_NEGATIVE_TYPES: frozenset[EvidenceType] = frozenset({
    EvidenceType.COMMUNICATION_GAP,
    EvidenceType.SHALLOW_ANSWER,
})

# Inconsistency indicators.
COMM_INCONSISTENT_TYPES: frozenset[EvidenceType] = frozenset({
    EvidenceType.CONTRADICTORY_ANSWER,
})


@dataclass(frozen=True)
class CommunicationStats:
    """Communication signal statistics for the COMMUNICATION dimension."""

    positive_count: int = 0
    negative_count: int = 0
    inconsistent_count: int = 0

    @property
    def total(self) -> int:
        return self.positive_count + self.negative_count + self.inconsistent_count

    @property
    def strength_ratio(self) -> float:
        """Returns [0.0, 1.0]; 0.5 when total == 0 (neutral)."""
        eligible = self.positive_count + self.negative_count
        if eligible == 0:
            return 0.5
        return self.positive_count / eligible

    @property
    def has_inconsistency(self) -> bool:
        return self.inconsistent_count > 0


class CommunicationObservationExtractor:
    """Extracts COMMUNICATION dimension signal statistics.

    Only signals with dimension == COMMUNICATION are considered.
    Single O(n) pass over the full EvidenceStore.
    """

    def analyze(self, signals: list[EvidenceSignal]) -> CommunicationStats:
        """Return CommunicationStats for COMMUNICATION dimension signals."""
        positive = 0
        negative = 0
        inconsistent = 0

        for sig in signals:
            if sig.dimension != ProfileDimension.COMMUNICATION:
                continue

            if sig.signal_type in COMM_POSITIVE_TYPES and sig.polarity == EvidencePolarity.POSITIVE:
                positive += 1
            elif sig.signal_type in COMM_NEGATIVE_TYPES and sig.polarity == EvidencePolarity.NEGATIVE:
                negative += 1
            elif sig.signal_type in COMM_INCONSISTENT_TYPES:
                inconsistent += 1

        return CommunicationStats(
            positive_count=positive,
            negative_count=negative,
            inconsistent_count=inconsistent,
        )
