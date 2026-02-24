# domain/contracts/performance_dimension.py

# Performance dimension contract
#
# Represents a single evaluation dimension of the interview.
# Responsibility: structured dimension-level assessment.

from pydantic import BaseModel, Field


class PerformanceDimension(BaseModel):
    name: str = Field(..., min_length=1)
    score: float = Field(..., ge=1.0, le=10.0)
    justification: str = Field(..., min_length=1)

    model_config = {"frozen": True}
