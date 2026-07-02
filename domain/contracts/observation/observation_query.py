# domain/contracts/observation/observation_query.py
# ADR-016: ObservationStore read interface — query object

from enum import Enum

from pydantic import BaseModel, Field

from domain.contracts.observation.observation_filter import ObservationFilter


class ObservationSortField(str, Enum):
    """Field to sort query results by."""

    QUESTION_INDEX = "question_index"
    OBSERVED_AT = "observed_at"
    CONFIDENCE = "confidence"
    WEIGHT = "weight"


class ObservationSortOrder(str, Enum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"


class ObservationQuery(BaseModel):
    """Immutable query specification passed to ObservationStore.query().

    Composes an ObservationFilter with pagination and ordering controls.

    Invariants:
    - limit must be in [1, 1000].
    - offset must be >= 0.
    - filter is required (use ObservationFilter() for no filtering).
    """

    filter: ObservationFilter = Field(default_factory=ObservationFilter)
    sort_by: ObservationSortField = Field(default=ObservationSortField.QUESTION_INDEX)
    sort_order: ObservationSortOrder = Field(default=ObservationSortOrder.ASC)
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
