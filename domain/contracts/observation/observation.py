# domain/contracts/observation/observation.py
# ADR-016: Observation — first-class domain object
# ADR-017: Immutability and lifecycle constraints

from pydantic import BaseModel, Field, field_validator

from domain.contracts.observation.observation_id import ObservationId
from domain.contracts.observation.observation_metadata import ObservationMetadata
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType


class Observation(BaseModel):
    """Immutable, typed, timestamped domain object produced by ObservationExtractor.

    Observations are the atomic unit of evidence in the Observation Intelligence
    Layer (ADR-016). They are derived exclusively from EvidenceSignals via
    ObservationExtractor (canonical flow, Section A-2 K2).

    Invariants:
    - Fully immutable once constructed (frozen=True, extra="forbid").
    - id is unique across the entire session.
    - description is a system-generated label; NEVER contains candidate text
      (ADR-035 security constraint, inherited).
    - confidence is in [0.0, 1.0].
    - weight is in (0.0, 1.0]; default 1.0; reduced by decay (ADR-021).
    - status begins as ACTIVE; transitions only via ObservationStore rules.
    - tags are optional, immutable labels for filtering / grouping.
    """

    id: ObservationId = Field(default_factory=ObservationId.generate)
    observation_type: ObservationType
    status: ObservationStatus = Field(default=ObservationStatus.ACTIVE)
    metadata: ObservationMetadata

    # System-generated descriptor — NEVER candidate-supplied text (ADR-035).
    description: str = Field(..., min_length=1, max_length=500)

    # Confidence in [0.0, 1.0] — how strongly the signal supports the type.
    confidence: float = Field(..., ge=0.0, le=1.0)

    # Decay weight in (0.0, 1.0]; updated by ObservationStore decay function (ADR-021).
    weight: float = Field(default=1.0, gt=0.0, le=1.0)

    # Optional immutable label set for downstream filtering (ADR-016).
    tags: frozenset[str] = Field(default_factory=frozenset)

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @field_validator("description")
    @classmethod
    def _strip_description(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("description must not be blank")
        return stripped

    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_tags(cls, v: object) -> frozenset[str]:
        if v is None:
            return frozenset()
        if isinstance(v, (list, set, tuple)):
            return frozenset(v)
        if isinstance(v, frozenset):
            return v
        raise ValueError(f"tags must be a collection of strings, got {type(v)}")

    def with_status(self, new_status: ObservationStatus) -> "Observation":
        """Return a new Observation with updated status (used by ObservationStore)."""
        data = self.model_dump()
        data["status"] = new_status
        return Observation.model_validate(data)

    def with_weight(self, new_weight: float) -> "Observation":
        """Return a new Observation with updated decay weight (used by ObservationStore)."""
        data = self.model_dump()
        data["weight"] = new_weight
        return Observation.model_validate(data)
