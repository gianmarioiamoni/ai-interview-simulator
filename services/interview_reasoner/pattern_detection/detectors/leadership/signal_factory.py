# services/interview_reasoner/pattern_detection/detectors/leadership/signal_factory.py
"""LeadershipSignalFactory — produces EvidenceSignals from leadership verdicts (M2-7H, DET-11).

Signal mapping (TDS §20.2.6):
  STRONG_LEADER     → LEADERSHIP_STRONG   / POSITIVE / strength = min(1.0, ratio * 1.5)
  EMERGING_LEADER   → LEADERSHIP_EMERGING / POSITIVE / strength = leadership_ratio
  LEADERSHIP_ABSENT → LEADERSHIP_ABSENT   / NEGATIVE / strength = 0.4 (fixed)
  NEUTRAL           → None

Per ADR-063: dimension = ProfileDimension.PROBLEM_SOLVING (V1.1 temporary mapping).
Signals are immutable; idempotency enforced by filter_new_signals upstream.
"""

from __future__ import annotations

import uuid

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.leadership.analyzer import (
    LeadershipStats,
)
from services.interview_reasoner.pattern_detection.detectors.leadership.scorer import (
    LeadershipVerdict,
)


class LeadershipSignalFactory:
    """Creates EvidenceSignals from LeadershipVerdict classifications."""

    def create(
        self,
        verdict: LeadershipVerdict,
        stats: LeadershipStats,
        question_index: int,
        area: str,
    ) -> EvidenceSignal | None:
        """Return the appropriate EvidenceSignal for the verdict, or None for NEUTRAL."""
        if verdict == LeadershipVerdict.STRONG_LEADER:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.PROBLEM_SOLVING,
                polarity=EvidencePolarity.POSITIVE,
                signal_type=EvidenceType.LEADERSHIP_STRONG,
                strength=round(min(1.0, stats.leadership_ratio * 1.5), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        if verdict == LeadershipVerdict.EMERGING_LEADER:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.PROBLEM_SOLVING,
                polarity=EvidencePolarity.POSITIVE,
                signal_type=EvidenceType.LEADERSHIP_EMERGING,
                strength=round(min(1.0, stats.leadership_ratio), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        if verdict == LeadershipVerdict.LEADERSHIP_ABSENT:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.PROBLEM_SOLVING,
                polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.LEADERSHIP_ABSENT,
                strength=0.4,
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        # NEUTRAL → no signal
        return None
