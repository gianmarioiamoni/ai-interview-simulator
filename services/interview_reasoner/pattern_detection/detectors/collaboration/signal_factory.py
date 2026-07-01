# services/interview_reasoner/pattern_detection/detectors/collaboration/signal_factory.py
"""CollaborationSignalFactory — produces EvidenceSignals from collaboration verdicts (M2-7I, DET-12).

Signal mapping (TDS §20.3.6):
  STRONG_COLLABORATOR    → COLLABORATION_STRONG    / POSITIVE / strength = min(1.0, ratio * 1.6)
  EFFECTIVE_COLLABORATOR → COLLABORATION_EFFECTIVE / POSITIVE / strength = collaboration_ratio
  COLLABORATION_DEFICIT  → COLLABORATION_DEFICIT   / NEGATIVE / strength = 0.45 (fixed)
  NEUTRAL                → None

Per ADR-064: dimension = ProfileDimension.COMMUNICATION (V1.1 temporary mapping).
Signals are immutable; idempotency enforced by filter_new_signals upstream.
Never generates LEADERSHIP_* or ADAPTABILITY_* signals.
"""

from __future__ import annotations

import uuid

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.collaboration.analyzer import (
    CollaborationStats,
)
from services.interview_reasoner.pattern_detection.detectors.collaboration.scorer import (
    CollaborationVerdict,
)


class CollaborationSignalFactory:
    """Creates EvidenceSignals from CollaborationVerdict classifications."""

    def create(
        self,
        verdict: CollaborationVerdict,
        stats: CollaborationStats,
        question_index: int,
        area: str,
    ) -> EvidenceSignal | None:
        """Return the appropriate EvidenceSignal for the verdict, or None for NEUTRAL."""
        if verdict == CollaborationVerdict.STRONG_COLLABORATOR:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.COMMUNICATION,
                polarity=EvidencePolarity.POSITIVE,
                signal_type=EvidenceType.COLLABORATION_STRONG,
                strength=round(min(1.0, stats.collaboration_ratio * 1.6), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        if verdict == CollaborationVerdict.EFFECTIVE_COLLABORATOR:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.COMMUNICATION,
                polarity=EvidencePolarity.POSITIVE,
                signal_type=EvidenceType.COLLABORATION_EFFECTIVE,
                strength=round(min(1.0, stats.collaboration_ratio), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        if verdict == CollaborationVerdict.COLLABORATION_DEFICIT:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.COMMUNICATION,
                polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.COLLABORATION_DEFICIT,
                strength=0.45,
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        # NEUTRAL → no signal
        return None
