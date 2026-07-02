# domain/contracts/observation/observation_filter.py
# ADR-016: ObservationStore read interface — filter predicate

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType


class ObservationFilter(BaseModel):
    """Immutable filter predicate for querying the ObservationStore.

    All fields are optional. Omitting a field means "match any value" for that
    dimension. Multiple fields are combined with AND semantics.

    Invariants:
    - question_index_min <= question_index_max when both are set.
    - observed_after < observed_before when both are set.
    - confidence_min <= confidence_max when both are set (both in [0.0, 1.0]).
    - weight_min <= weight_max when both are set (both in (0.0, 1.0]).
    """

    observation_types: frozenset[ObservationType] | None = Field(
        default=None,
        description="Match any of these types; None = match all types",
    )
    statuses: frozenset[ObservationStatus] | None = Field(
        default=None,
        description="Match any of these statuses; None = match all statuses",
    )
    origins: frozenset[ObservationOrigin] | None = Field(
        default=None,
        description="Match any of these origins; None = match all origins",
    )
    question_index_min: int | None = Field(default=None, ge=0)
    question_index_max: int | None = Field(default=None, ge=0)
    observed_after: datetime | None = Field(default=None)
    observed_before: datetime | None = Field(default=None)
    confidence_min: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_max: float | None = Field(default=None, ge=0.0, le=1.0)
    weight_min: float | None = Field(default=None, gt=0.0, le=1.0)
    weight_max: float | None = Field(default=None, gt=0.0, le=1.0)
    tags_any: frozenset[str] | None = Field(
        default=None,
        description="Match observations that have at least one of these tags",
    )
    tags_all: frozenset[str] | None = Field(
        default=None,
        description="Match observations that have ALL of these tags",
    )
    session_id: str | None = Field(default=None, description="Restrict to a single session")

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def _validate_range_consistency(self) -> "ObservationFilter":
        if (
            self.question_index_min is not None
            and self.question_index_max is not None
            and self.question_index_min > self.question_index_max
        ):
            raise ValueError("question_index_min must be <= question_index_max")

        if (
            self.observed_after is not None
            and self.observed_before is not None
            and self.observed_after >= self.observed_before
        ):
            raise ValueError("observed_after must be strictly before observed_before")

        if (
            self.confidence_min is not None
            and self.confidence_max is not None
            and self.confidence_min > self.confidence_max
        ):
            raise ValueError("confidence_min must be <= confidence_max")

        if (
            self.weight_min is not None
            and self.weight_max is not None
            and self.weight_min > self.weight_max
        ):
            raise ValueError("weight_min must be <= weight_max")

        return self
