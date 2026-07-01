# services/interview_reasoner/pattern_detection/detectors/consistency_across_interview/signal_factory.py
"""ConsistencySignalFactory — produces EvidenceSignals from consistency verdicts (M2-7D, DET-09).

All signals:
  - source = EvidenceSource.PATTERN_DETECTOR
  - dimension = the dimension where the cross-area finding applies
  - subject to filter_new_signals (idempotency)

Signal mapping (TDS DET-09):
  CONTRADICTORY → CROSS_AREA_CONTRADICTORY (negative)
  CONSISTENT    → CROSS_AREA_CONSISTENT (positive)
  NEUTRAL       → None

Future V1.2: ConsistencyObservation enriches CrossDomainConsistencyFeature.
"""

from __future__ import annotations

import uuid

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview.analyzer import (
    CrossAreaResult,
)
from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview.scorer import (
    ConsistencyVerdict,
)


class ConsistencySignalFactory:
    """Creates EvidenceSignals from ConsistencyVerdict classifications."""

    def make_signal(
        self,
        verdict: ConsistencyVerdict,
        result: CrossAreaResult,
        question_index: int,
        area: str,
    ) -> EvidenceSignal | None:
        """Return a cross-area EvidenceSignal or None for NEUTRAL."""
        if verdict == ConsistencyVerdict.CONTRADICTORY:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=result.dimension,
                polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.CROSS_AREA_CONTRADICTORY,
                strength=round(min(result.max_ratio_delta, 1.0), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        if verdict == ConsistencyVerdict.CONSISTENT:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=result.dimension,
                polarity=EvidencePolarity.POSITIVE,
                signal_type=EvidenceType.CROSS_AREA_CONSISTENT,
                strength=round(min(1.0 - result.max_ratio_delta, 1.0), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        return None
