# services/interview_reasoner/pattern_detection/detectors/adaptability/signal_factory.py
"""AdaptabilitySignalFactory — produces EvidenceSignals from adaptability verdicts (M2-7J, DET-13).

Signal mapping (TDS §20.4.6):
  HIGHLY_ADAPTABLE → ADAPTABILITY_HIGH     / POSITIVE / strength = min(1.0, adaptability_ratio * 1.3)
  ADAPTABLE        → ADAPTABILITY_MODERATE / POSITIVE / strength = max(adaptability_ratio, flexibility_ratio)
  LOW_ADAPTABILITY → ADAPTABILITY_LOW      / NEGATIVE / strength = min(1.0, rigidity_count / 5.0)
  NEUTRAL          → None

Dimension: ProfileDimension.PROBLEM_SOLVING (V1.1 temporary mapping).
Signals are immutable; idempotency enforced by filter_new_signals upstream.
Never generates Leadership, Collaboration, Communication, or Engineering signals.
"""

from __future__ import annotations

import uuid

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.adaptability.analyzer import (
    AdaptabilityStats,
)
from services.interview_reasoner.pattern_detection.detectors.adaptability.scorer import (
    AdaptabilityVerdict,
)


class AdaptabilitySignalFactory:
    """Creates EvidenceSignals from AdaptabilityVerdict classifications."""

    def create(
        self,
        verdict: AdaptabilityVerdict,
        stats: AdaptabilityStats,
        question_index: int,
        area: str,
    ) -> EvidenceSignal | None:
        """Return the appropriate EvidenceSignal for the verdict, or None for NEUTRAL."""
        if verdict == AdaptabilityVerdict.HIGHLY_ADAPTABLE:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.PROBLEM_SOLVING,
                polarity=EvidencePolarity.POSITIVE,
                signal_type=EvidenceType.ADAPTABILITY_HIGH,
                strength=round(min(1.0, stats.adaptability_ratio * 1.3), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        if verdict == AdaptabilityVerdict.ADAPTABLE:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.PROBLEM_SOLVING,
                polarity=EvidencePolarity.POSITIVE,
                signal_type=EvidenceType.ADAPTABILITY_MODERATE,
                strength=round(min(1.0, max(stats.adaptability_ratio, stats.flexibility_ratio)), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        if verdict == AdaptabilityVerdict.LOW_ADAPTABILITY:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.PROBLEM_SOLVING,
                polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.ADAPTABILITY_LOW,
                strength=round(min(1.0, stats.rigidity_count / 5.0), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        # NEUTRAL → no signal
        return None
