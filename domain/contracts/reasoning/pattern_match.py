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
    """Aggregated pipeline output for one ReasonerService cycle (ADR-034).

    Merges all DetectorResult records from every active detector.
    Consumed by ReasonerService to build the ReasonerDecision.
    """

    matches: list[PatternMatch] = Field(default_factory=list)
    generated_signals: list[EvidenceSignal] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0, ge=0.0)
    warnings: list[str] = Field(default_factory=list)

    @property
    def all_evidence(self) -> list[EvidenceSignal]:
        return list(self.generated_signals)

    @property
    def detected_types(self) -> list[EvidenceType]:
        """Return all EvidenceTypes present in matches + generated_signals (deduplicated)."""
        types_from_matches = [m.pattern_type for m in self.matches]
        types_from_signals = [s.signal_type for s in self.generated_signals]
        # Preserve order, deduplicate
        seen: set[EvidenceType] = set()
        result: list[EvidenceType] = []
        for t in types_from_matches + types_from_signals:
            if t not in seen:
                seen.add(t)
                result.append(t)
        return result

    model_config = {"frozen": True, "extra": "forbid"}
