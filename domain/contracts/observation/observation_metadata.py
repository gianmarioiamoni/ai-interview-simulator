# domain/contracts/observation/observation_metadata.py
# ADR-016: Observation schema — metadata envelope
# ADR-017: Temporal semantics — TTL anchoring

from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator, model_validator

from domain.contracts.observation.observation_origin import ObservationOrigin


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class ObservationMetadata(BaseModel):
    """Immutable envelope describing when and how an Observation was produced.

    Invariants (ADR-016, ADR-017):
    - observed_at is UTC; must not be in the future at construction.
    - question_index >= 0; anchors the observation to a specific turn.
    - session_id identifies the owning session (non-empty).
    - source_ref is an opaque reference to the originating artefact
      (EvidenceSignal id, EvaluationResult id, etc.); may be None when origin
      is REPLAY or CALIBRATION.
    - extractor_version records the ObservationExtractor version that produced
      this Observation for auditability.
    """

    observed_at: datetime = Field(default_factory=_utcnow)
    question_index: int = Field(..., ge=0, description="Session turn index (0-based)")
    session_id: str = Field(..., min_length=1, description="Owning session identifier")
    origin: ObservationOrigin
    source_ref: str | None = Field(
        default=None,
        description="Opaque reference to the originating artefact; None for REPLAY/CALIBRATION",
    )
    extractor_version: str = Field(
        default="1.0",
        min_length=1,
        description="ObservationExtractor version that produced this observation",
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @field_validator("observed_at", mode="before")
    @classmethod
    def _normalise_timezone(cls, v: datetime | str) -> datetime:
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @model_validator(mode="after")
    def _source_ref_required_for_runtime_origins(self) -> "ObservationMetadata":
        runtime_origins = {ObservationOrigin.EVALUATION, ObservationOrigin.EVIDENCE_SIGNAL, ObservationOrigin.PATTERN_DETECTOR}
        if self.origin in runtime_origins and self.source_ref is None:
            raise ValueError(
                f"source_ref is required for origin={self.origin!r}; "
                "only REPLAY and CALIBRATION may omit it."
            )
        return self
