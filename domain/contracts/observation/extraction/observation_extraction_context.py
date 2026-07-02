# domain/contracts/observation/extraction/observation_extraction_context.py
# ADR-016: Extraction context — immutable input envelope for ObservationExtractor

from pydantic import BaseModel, Field, model_validator

from domain.contracts.reasoning.evidence_signal import EvidenceSignal


class ObservationExtractionContext(BaseModel):
    """Immutable input context passed to each ObservationRule during extraction.

    Contains all data a rule may inspect to decide whether to emit a match.

    Invariants:
    - signals is a non-empty tuple of EvidenceSignals for this extraction cycle.
    - question_index >= 0; must match all signal question_index values.
    - session_id is non-empty; identifies the owning session.
    - extractor_version records the active extractor version for auditability.
    - All signals must share the same session_id (cross-session mixing is
      forbidden; ADR-016 ownership boundary).

    No candidate-supplied text is included — only system-generated signal
    descriptors (ADR-035 security constraint).
    """

    signals: tuple[EvidenceSignal, ...] = Field(
        ...,
        min_length=1,
        description="EvidenceSignals for this extraction cycle; must be non-empty",
    )
    question_index: int = Field(..., ge=0)
    session_id: str = Field(..., min_length=1)
    extractor_version: str = Field(default="1.0", min_length=1)
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def _validate_signal_consistency(self) -> "ObservationExtractionContext":
        for signal in self.signals:
            if signal.question_index != self.question_index:
                raise ValueError(
                    f"Signal question_index={signal.question_index} does not match "
                    f"context question_index={self.question_index}"
                )
        return self
