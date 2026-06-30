# domain/contracts/reasoning/pattern_match.py

from pydantic import BaseModel, Field

from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_type import EvidenceType


class PatternMatch(BaseModel):
    """Single pattern match produced by one PatternDetector rule.

    Contains only the evidence produced — no candidate text.
    """

    pattern_type: EvidenceType
    evidence_signals: list[EvidenceSignal] = Field(default_factory=list)
    # Detector-generated label; NEVER contains candidate-supplied text.
    label: str = Field(default="", max_length=200)

    model_config = {"frozen": True, "extra": "forbid"}


class PatternDetectionResult(BaseModel):
    """Aggregated output of the PatternDetectionPipeline for one cycle.

    All matches from all active detectors are merged here.
    """

    matches: list[PatternMatch] = Field(default_factory=list)

    @property
    def all_evidence(self) -> list[EvidenceSignal]:
        return [sig for m in self.matches for sig in m.evidence_signals]

    @property
    def detected_types(self) -> list[EvidenceType]:
        return [m.pattern_type for m in self.matches]

    model_config = {"frozen": True, "extra": "forbid"}
