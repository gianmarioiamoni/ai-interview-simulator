# services/interview_reasoner/pattern_detection/detectors/engineering_judgment/analyzer.py
"""EngineeringJudgmentAnalyzer — classifies EvidenceStore signals for judgment dimension (M2-7C).

Responsibility: Identify signals belonging to the ENGINEERING_JUDGMENT dimension
and compute per-dimension judgment stats.

Judgment-positive signals (POSITIVE polarity only):
  - ENGINEERING_JUDGMENT_ARTICULATED
  - DEMONSTRATED_DEPTH on ENGINEERING_JUDGMENT dim

Judgment-negative signals (NEGATIVE polarity only):
  - SHALLOW_ANSWER on ENGINEERING_JUDGMENT dim
  - REASONING_GAP on ENGINEERING_JUDGMENT dim
  - KNOWLEDGE_GAP on ENGINEERING_JUDGMENT dim

O(n) single pass.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension

# Positive judgment signal types (require POSITIVE polarity).
JUDGMENT_POSITIVE_TYPES: frozenset[EvidenceType] = frozenset({
    EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED,
    EvidenceType.DEMONSTRATED_DEPTH,
})

# Negative judgment signal types (require NEGATIVE polarity).
JUDGMENT_NEGATIVE_TYPES: frozenset[EvidenceType] = frozenset({
    EvidenceType.SHALLOW_ANSWER,
    EvidenceType.REASONING_GAP,
    EvidenceType.KNOWLEDGE_GAP,
})


@dataclass(frozen=True)
class JudgmentStats:
    """Judgment signal statistics for the ENGINEERING_JUDGMENT dimension."""

    positive_count: int = 0
    negative_count: int = 0
    # Total evaluation-origin signals for the dimension (guard against phantom signals).
    evaluation_signal_count: int = 0

    @property
    def total(self) -> int:
        return self.positive_count + self.negative_count

    @property
    def judgment_ratio(self) -> float:
        """Returns [0.0, 1.0]; 0.5 when total == 0 (neutral)."""
        if self.total == 0:
            return 0.5
        return self.positive_count / self.total


class EngineeringJudgmentAnalyzer:
    """Classifies EvidenceSignals for the ENGINEERING_JUDGMENT dimension.

    Only signals with dimension == ENGINEERING_JUDGMENT are considered.
    Single O(n) pass over the full EvidenceStore.
    """

    def analyze(self, signals: list[EvidenceSignal]) -> JudgmentStats:
        """Return JudgmentStats for ENGINEERING_JUDGMENT dimension signals."""
        from domain.contracts.reasoning.evidence_source import EvidenceSource

        positive = 0
        negative = 0
        eval_count = 0

        for sig in signals:
            if sig.dimension != ProfileDimension.ENGINEERING_JUDGMENT:
                continue

            if sig.source == EvidenceSource.EVALUATION:
                eval_count += 1

            if sig.signal_type in JUDGMENT_POSITIVE_TYPES and sig.polarity == EvidencePolarity.POSITIVE:
                positive += 1
            elif sig.signal_type in JUDGMENT_NEGATIVE_TYPES and sig.polarity == EvidencePolarity.NEGATIVE:
                negative += 1

        return JudgmentStats(
            positive_count=positive,
            negative_count=negative,
            evaluation_signal_count=eval_count,
        )
