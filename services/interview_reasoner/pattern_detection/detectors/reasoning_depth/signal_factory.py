# services/interview_reasoner/pattern_detection/detectors/reasoning_depth/signal_factory.py
"""ReasoningDepthSignalFactory — produces EvidenceSignals from depth verdicts (M2-7B).

Responsibility: map DepthVerdict + DimensionDepthStats → EvidenceSignal.

All signals produced here:
  - source = EvidenceSource.PATTERN_DETECTOR
  - subject to filter_new_signals (idempotency)
  - strength derived from depth_ratio
"""

from __future__ import annotations

import uuid

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.reasoning_depth.analyzer import (
    DimensionDepthStats,
)
from services.interview_reasoner.pattern_detection.detectors.reasoning_depth.scorer import (
    DepthVerdict,
)


class ReasoningDepthSignalFactory:
    """Creates EvidenceSignals from DepthVerdict classifications."""

    def make_depth_signal(
        self,
        verdict: DepthVerdict,
        stats: DimensionDepthStats,
        question_index: int,
        area: str,
    ) -> EvidenceSignal | None:
        """Return a REASONING_DEPTH_HIGH or REASONING_DEPTH_LOW signal, or None."""
        if verdict == DepthVerdict.HIGH:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=stats.dimension,
                polarity=EvidencePolarity.POSITIVE,
                signal_type=EvidenceType.REASONING_DEPTH_HIGH,
                strength=round(min(stats.depth_ratio, 1.0), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        if verdict == DepthVerdict.LOW:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=stats.dimension,
                polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.REASONING_DEPTH_LOW,
                strength=round(min(1.0 - stats.depth_ratio, 1.0), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        return None

    def make_trend_signal(
        self,
        trend: DepthVerdict,
        dimension: ProfileDimension,
        question_index: int,
        area: str,
        strength: float = 0.6,
    ) -> EvidenceSignal | None:
        """Return a REASONING_IMPROVING or REASONING_STAGNATING signal, or None."""
        if trend == DepthVerdict.IMPROVING:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=dimension,
                polarity=EvidencePolarity.POSITIVE,
                signal_type=EvidenceType.REASONING_IMPROVING,
                strength=round(strength, 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        if trend == DepthVerdict.LOW:  # LOW verdict → stagnating trend
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=dimension,
                polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.REASONING_STAGNATING,
                strength=round(strength, 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        return None
