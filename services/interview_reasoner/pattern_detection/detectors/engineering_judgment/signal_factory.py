# services/interview_reasoner/pattern_detection/detectors/engineering_judgment/signal_factory.py
"""EngineeringJudgmentSignalFactory — produces EvidenceSignals from judgment verdicts (M2-7C).

All signals:
  - source = EvidenceSource.PATTERN_DETECTOR
  - dimension = ProfileDimension.ENGINEERING_JUDGMENT
  - subject to filter_new_signals (idempotency)
"""

from __future__ import annotations

import uuid

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.engineering_judgment.analyzer import (
    JudgmentStats,
)
from services.interview_reasoner.pattern_detection.detectors.engineering_judgment.scorer import (
    JudgmentVerdict,
)


class EngineeringJudgmentSignalFactory:
    """Creates EvidenceSignals from JudgmentVerdict classifications."""

    def make_signal(
        self,
        verdict: JudgmentVerdict,
        stats: JudgmentStats,
        question_index: int,
        area: str,
    ) -> EvidenceSignal | None:
        """Return ENGINEERING_JUDGMENT_HIGH or ENGINEERING_JUDGMENT_LOW signal, or None."""
        if verdict == JudgmentVerdict.HIGH:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.ENGINEERING_JUDGMENT,
                polarity=EvidencePolarity.POSITIVE,
                signal_type=EvidenceType.ENGINEERING_JUDGMENT_HIGH,
                strength=round(min(stats.judgment_ratio, 1.0), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        if verdict == JudgmentVerdict.LOW:
            return EvidenceSignal(
                id=str(uuid.uuid4()),
                question_index=question_index,
                question_area=area,
                dimension=ProfileDimension.ENGINEERING_JUDGMENT,
                polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.ENGINEERING_JUDGMENT_LOW,
                strength=round(min(1.0 - stats.judgment_ratio, 1.0), 4),
                source=EvidenceSource.PATTERN_DETECTOR,
                timestamp_question_index=question_index,
            )
        return None
