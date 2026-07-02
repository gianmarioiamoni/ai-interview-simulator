# domain/contracts/observation/observation_id.py
# ADR-016: Observation schema — identity model

import uuid
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


def _new_uuid() -> str:
    return str(uuid.uuid4())


class ObservationId(BaseModel):
    """Stable, opaque identity for a single Observation.

    Immutable once assigned. Format is UUID-v4 string.
    Two ObservationIds are equal iff their `value` fields are equal.

    Invariants (ADR-016):
    - value must be a valid UUID-v4 string.
    - value is assigned at creation; never re-assigned.
    """

    value: str = Field(default_factory=_new_uuid, min_length=36, max_length=36)
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @field_validator("value")
    @classmethod
    def _must_be_uuid(cls, v: str) -> str:
        try:
            uuid.UUID(v, version=4)
        except ValueError as exc:
            raise ValueError(f"ObservationId.value must be a valid UUID-v4: {v!r}") from exc
        return v

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ObservationId):
            return self.value == other.value
        return NotImplemented

    @classmethod
    def generate(cls) -> "ObservationId":
        """Factory: produce a fresh unique ObservationId."""
        return cls(value=_new_uuid())
