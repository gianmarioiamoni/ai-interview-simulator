# services/interview_reasoner/pattern_detection/detectors/behavioral_pattern/signal_factory.py
"""BehaviorSignalFactory — produces EvidenceSignals from behavioral verdicts (M2-7D).

All signals:
  - source = EvidenceSource.PATTERN_DETECTOR
  - dimension = ProfileDimension.PROBLEM_SOLVING (behavioral proxy dimension)
  - subject to filter_new_signals (idempotency)

Signal mapping (TDS DET-08):
  GROWTH      → BEHAVIORAL_GROWTH (positive)
  INSTABILITY → BEHAVIORAL_INSTABILITY (negative)
  PLATEAU     → BEHAVIORAL_PLATEAU (neutral / negative)
  NEUTRAL     → None

Future V1.2: Observation carries description text for CoachingEngine.
"""

from __future__ import annotations

import uuid

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern.analyzer import (
    BehavioralStats,
)
from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern.scorer import (
    BehaviorVerdict,
)

# Behavioral signals are attributed to PROBLEM_SOLVING as the dimension that
# most closely represents meta-cognitive and adaptive behavior.
_BEHAVIORAL_DIM = ProfileDimension.PROBLEM_SOLVING


class BehaviorSignalFactory:
    """Creates EvidenceSignals from BehaviorVerdict classifications."""

    def make_signal(
        self,
        verdict: BehaviorVerdict,
        stats: BehavioralStats,
        question_index: int,
        area: str,
    ) -> EvidenceSignal | None:
        """Return a behavioral EvidenceSignal or None for NEUTRAL."""
        if verdict == BehaviorVerdict.GROWTH:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=_BEHAVIORAL_DIM,
                polarity=EvidencePolarity.POSITIVE,
                signal_type=EvidenceType.BEHAVIORAL_GROWTH,
                strength=round(min(stats.positive_ratio + 0.1, 1.0), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        if verdict == BehaviorVerdict.INSTABILITY:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=_BEHAVIORAL_DIM,
                polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.BEHAVIORAL_INSTABILITY,
                strength=round(min(stats.variance_score, 1.0), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        if verdict == BehaviorVerdict.PLATEAU:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=_BEHAVIORAL_DIM,
                polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.BEHAVIORAL_PLATEAU,
                strength=0.4,
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        return None
