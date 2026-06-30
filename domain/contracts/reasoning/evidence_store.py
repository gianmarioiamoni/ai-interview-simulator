# domain/contracts/reasoning/evidence_store.py

from pydantic import BaseModel, Field

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension

_MAX_SIGNALS = 200


class EvidenceStore(BaseModel):
    """Append-only canonical store of EvidenceSignal for the session.

    Capped at MAX_SIGNALS (200) entries.
    Provides query helper properties — all read-only.
    Single-writer: InterviewReasoner (ADR-032, ADR-038).
    """

    signals: list[EvidenceSignal] = Field(
        default_factory=list,
        max_length=_MAX_SIGNALS,
    )

    model_config = {"frozen": True, "extra": "forbid"}

    def positive(self) -> list[EvidenceSignal]:
        return [s for s in self.signals if s.polarity == EvidencePolarity.POSITIVE]

    def negative(self) -> list[EvidenceSignal]:
        return [s for s in self.signals if s.polarity == EvidencePolarity.NEGATIVE]

    def by_dimension(self, dim: ProfileDimension) -> list[EvidenceSignal]:
        return [s for s in self.signals if s.dimension == dim]

    def by_type(self, evidence_type: EvidenceType) -> list[EvidenceSignal]:
        return [s for s in self.signals if s.signal_type == evidence_type]

    def by_source(self, source: EvidenceSource) -> list[EvidenceSignal]:
        return [s for s in self.signals if s.source == source]

    def strength_above(self, threshold: float) -> list[EvidenceSignal]:
        return [s for s in self.signals if s.strength >= threshold]
