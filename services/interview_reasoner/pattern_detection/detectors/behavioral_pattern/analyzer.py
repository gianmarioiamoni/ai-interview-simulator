# services/interview_reasoner/pattern_detection/detectors/behavioral_pattern/analyzer.py
"""BehaviorObservationExtractor — classifies ReasoningHistory for behavioral patterns (M2-7D).

Responsibility: Scan history entries and identify behavioral trends:
  - Confidence evolution (reasoning_confidence trajectory)
  - Pattern stability (detected_patterns changing vs. stable)
  - Growth indicators (positive pattern types increasing)
  - Instability indicators (high variance in pattern types)

O(n) single pass over history entries.

Future V1.2 Observation type: BehavioralObservation
Future ProfileFeature: BehavioralPatternFeature
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.reasoning_history import ReasoningEntry

# Positive pattern types that indicate behavioral strength.
POSITIVE_PATTERN_TYPES: frozenset[EvidenceType] = frozenset({
    EvidenceType.REPEATED_STRENGTH,
    EvidenceType.RECOVERED_WEAKNESS,
    EvidenceType.DEMONSTRATED_DEPTH,
    EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED,
    EvidenceType.REASONING_IMPROVING,
    EvidenceType.REASONING_DEPTH_HIGH,
})

# Negative pattern types that indicate behavioral weakness.
NEGATIVE_PATTERN_TYPES: frozenset[EvidenceType] = frozenset({
    EvidenceType.REPEATED_WEAKNESS,
    EvidenceType.SHALLOW_ANSWER,
    EvidenceType.KNOWLEDGE_GAP,
    EvidenceType.REASONING_GAP,
    EvidenceType.REASONING_STAGNATING,
    EvidenceType.REASONING_DEPTH_LOW,
})

# Minimum entries required before any behavioral verdict is emitted.
MIN_ENTRIES = 3


@dataclass(frozen=True)
class BehavioralStats:
    """Behavioral statistics derived from ReasoningHistory.

    Future V1.2: will be promoted to BehavioralObservation with description field.
    """

    entry_count: int = 0
    confidence_trend: float = 0.0   # positive = growing, negative = declining
    positive_ratio: float = 0.0     # share of positive pattern types across all entries
    variance_score: float = 0.0     # 0.0 = stable, 1.0 = maximally erratic
    has_growth: bool = False         # confidence improving AND positive_ratio high
    has_instability: bool = False    # high variance in patterns
    has_plateau: bool = False        # confidence stable, neither improving nor declining


class BehaviorObservationExtractor:
    """Extracts behavioral statistics from ReasoningHistory.

    Single O(n) pass over history entries.
    Does NOT read EvidenceStore — behavioral analysis is history-only.
    """

    def analyze(self, entries: list[ReasoningEntry]) -> BehavioralStats:
        """Return BehavioralStats from history entries."""
        n = len(entries)
        if n < MIN_ENTRIES:
            return BehavioralStats(entry_count=n)

        confidences = [e.reasoning_confidence for e in entries]
        confidence_trend = self._compute_trend(confidences)

        total_patterns = 0
        positive_count = 0
        pattern_sets: list[frozenset[EvidenceType]] = []

        for entry in entries:
            pts = frozenset(entry.detected_patterns)
            pattern_sets.append(pts)
            total_patterns += len(pts)
            positive_count += sum(1 for pt in pts if pt in POSITIVE_PATTERN_TYPES)

        positive_ratio = positive_count / max(total_patterns, 1)
        variance_score = self._compute_variance(pattern_sets)

        has_growth = confidence_trend > 0.05 and positive_ratio > 0.4
        has_instability = variance_score > 0.55
        has_plateau = abs(confidence_trend) <= 0.05 and not has_instability

        return BehavioralStats(
            entry_count=n,
            confidence_trend=round(confidence_trend, 4),
            positive_ratio=round(positive_ratio, 4),
            variance_score=round(variance_score, 4),
            has_growth=has_growth,
            has_instability=has_instability,
            has_plateau=has_plateau,
        )

    def _compute_trend(self, values: list[float]) -> float:
        """Return slope proxy: mean of consecutive differences.

        Positive → improving, negative → declining.
        O(n).
        """
        if len(values) < 2:
            return 0.0
        diffs = [values[i + 1] - values[i] for i in range(len(values) - 1)]
        return sum(diffs) / len(diffs)

    def _compute_variance(self, pattern_sets: list[frozenset[EvidenceType]]) -> float:
        """Jaccard-based variance: mean pairwise dissimilarity between consecutive sets.

        O(n) — only consecutive pairs, not all pairs.
        Returns 0.0 (identical) to 1.0 (completely different).
        """
        if len(pattern_sets) < 2:
            return 0.0
        scores: list[float] = []
        for i in range(len(pattern_sets) - 1):
            a, b = pattern_sets[i], pattern_sets[i + 1]
            union = len(a | b)
            intersection = len(a & b)
            dissimilarity = 1.0 - (intersection / union) if union > 0 else 0.0
            scores.append(dissimilarity)
        return sum(scores) / len(scores)
