# services/interview_reasoner/pattern_detection/detectors/communication/signal_factory.py
"""CommunicationSignalFactory — produces EvidenceSignals from communication verdicts (M2-7C).

All signals:
  - source = EvidenceSource.PATTERN_DETECTOR
  - dimension = ProfileDimension.COMMUNICATION
  - subject to filter_new_signals (idempotency)

Signal mapping:
  CLEAR        → COMMUNICATION_CLEAR (positive)
  WEAK         → COMMUNICATION_WEAK  (negative)  [maps to COMMUNICATION_GAP PatternMatch]
  INCONSISTENT → COMMUNICATION_INCONSISTENT (negative) [maps to CONTRADICTORY_ANSWER PatternMatch]
"""

from __future__ import annotations

import uuid

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.communication.scorer import (
    CommunicationVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.communication.analyzer import (
    CommunicationStats,
)


class CommunicationSignalFactory:
    """Creates EvidenceSignals from CommunicationVerdict classifications."""

    def make_signal(
        self,
        verdict: CommunicationVerdict,
        stats: CommunicationStats,
        question_index: int,
        area: str,
    ) -> EvidenceSignal | None:
        """Return a communication signal for the given verdict, or None for NEUTRAL."""
        if verdict == CommunicationVerdict.CLEAR:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.COMMUNICATION,
                polarity=EvidencePolarity.POSITIVE,
                signal_type=EvidenceType.COMMUNICATION_CLEAR,
                strength=round(min(stats.strength_ratio, 1.0), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        if verdict == CommunicationVerdict.WEAK:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.COMMUNICATION,
                polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.COMMUNICATION_WEAK,
                strength=round(min(1.0 - stats.strength_ratio, 1.0), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        if verdict == CommunicationVerdict.INCONSISTENT:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.COMMUNICATION,
                polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.COMMUNICATION_INCONSISTENT,
                strength=round(
                    min(stats.inconsistent_count / max(stats.total, 1), 1.0), 4
                ),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        return None
