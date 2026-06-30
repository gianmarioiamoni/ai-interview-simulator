# domain/contracts/reasoning/evidence_store.py

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension

_MAX_SIGNALS = 200


class EvidenceStoreStatistics(BaseModel):
    """Aggregate statistics over all EvidenceSignals in an EvidenceStore (ADR-046)."""

    total: int
    positive: int
    negative: int
    per_dimension: dict[str, int]
    per_type: dict[str, int]
    mean_strength: float
    mean_strength_positive: float
    mean_strength_negative: float

    model_config = {"frozen": True, "extra": "forbid"}


class EvidenceStore(BaseModel):
    """Single point of access for all EvidenceSignal queries (ADR-046).

    Append-only; capped at _MAX_SIGNALS (200).
    All methods are O(n), deterministic, side-effect-free.
    Single-writer: InterviewReasoner (ADR-032, ADR-038).
    """

    signals: list[EvidenceSignal] = Field(
        default_factory=list,
        max_length=_MAX_SIGNALS,
    )

    model_config = {"frozen": True, "extra": "forbid"}

    # ------------------------------------------------------------------
    # Factory (immutable-friendly mutation)
    # ------------------------------------------------------------------

    def append(self, signal: EvidenceSignal) -> EvidenceStore:
        """Return a new EvidenceStore with `signal` appended.

        Preserves immutability: does not mutate self.
        Raises ValueError if capacity (_MAX_SIGNALS) would be exceeded.
        """
        if len(self.signals) >= _MAX_SIGNALS:
            raise ValueError(
                f"EvidenceStore capacity {_MAX_SIGNALS} exceeded; "
                "cannot append further signals."
            )
        return EvidenceStore(signals=[*self.signals, signal])

    # ------------------------------------------------------------------
    # Filters (all O(n), return new list)
    # ------------------------------------------------------------------

    def positive(self) -> list[EvidenceSignal]:
        return [s for s in self.signals if s.polarity == EvidencePolarity.POSITIVE]

    def negative(self) -> list[EvidenceSignal]:
        return [s for s in self.signals if s.polarity == EvidencePolarity.NEGATIVE]

    def by_dimension(self, dim: ProfileDimension) -> list[EvidenceSignal]:
        return [s for s in self.signals if s.dimension == dim]

    def by_question(self, question_index: int) -> list[EvidenceSignal]:
        return [s for s in self.signals if s.question_index == question_index]

    def by_type(self, evidence_type: EvidenceType) -> list[EvidenceSignal]:
        return [s for s in self.signals if s.signal_type == evidence_type]

    def by_source(self, source: EvidenceSource) -> list[EvidenceSignal]:
        return [s for s in self.signals if s.source == source]

    def strength_above(self, threshold: float) -> list[EvidenceSignal]:
        return [s for s in self.signals if s.strength >= threshold]

    def recent(self, n: int) -> list[EvidenceSignal]:
        """Return up to `n` most recent signals ordered by timestamp_question_index desc."""
        if n <= 0:
            return []
        sorted_signals = sorted(
            self.signals,
            key=lambda s: s.timestamp_question_index,
            reverse=True,
        )
        return sorted_signals[:n]

    # ------------------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------------------

    def statistics(self) -> EvidenceStoreStatistics:
        """Return aggregate statistics over all signals (ADR-046)."""
        total = len(self.signals)
        positive_sigs = self.positive()
        negative_sigs = self.negative()

        per_dimension: dict[str, int] = {}
        per_type: dict[str, int] = {}
        strength_sum = 0.0
        pos_strength_sum = 0.0
        neg_strength_sum = 0.0

        for s in self.signals:
            dim_key = s.dimension.value
            per_dimension[dim_key] = per_dimension.get(dim_key, 0) + 1
            type_key = s.signal_type.value
            per_type[type_key] = per_type.get(type_key, 0) + 1
            strength_sum += s.strength
            if s.polarity == EvidencePolarity.POSITIVE:
                pos_strength_sum += s.strength
            else:
                neg_strength_sum += s.strength

        pos_count = len(positive_sigs)
        neg_count = len(negative_sigs)

        return EvidenceStoreStatistics(
            total=total,
            positive=pos_count,
            negative=neg_count,
            per_dimension=per_dimension,
            per_type=per_type,
            mean_strength=round(strength_sum / total, 4) if total else 0.0,
            mean_strength_positive=round(pos_strength_sum / pos_count, 4) if pos_count else 0.0,
            mean_strength_negative=round(neg_strength_sum / neg_count, 4) if neg_count else 0.0,
        )
