# domain/contracts/report/scoring_dimension.py

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType

_VALID_LEVELS = frozenset({"strong", "moderate", "weak"})


class ScoringDimension(BaseModel):
    """Immutable per-dimension scoring record.

    A Projection Artifact (OP-02): carries computed scoring data for one
    performance dimension. Produced by ScoringSnapshotBuilder from
    InterviewEvaluationService output; never computed here.
    """

    model_config = {"frozen": True, "extra": "forbid"}

    dimension_type: PerformanceDimensionType
    score: float = Field(ge=0.0, le=100.0)
    signal: float = Field(ge=0.0, le=1.0)
    weighted_contribution: float = Field(ge=0.0, le=1.0)
    justification: str = Field(min_length=1)
    level: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_level(self) -> "ScoringDimension":
        if self.level not in _VALID_LEVELS:
            raise ValueError(
                f"level must be one of {sorted(_VALID_LEVELS)!r}; got {self.level!r}"
            )
        return self
