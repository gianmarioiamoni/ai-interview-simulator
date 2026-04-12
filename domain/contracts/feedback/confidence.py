# domain/contracts/confidence.py

# Confidence contract
#
# Represents model confidence in the evaluation process.
#
# base  -> confidence at question level (LLM certainty)
# final -> aggregated post-interview confidence
#
# Responsibility:
# - immutable value object
# - strict bounds validation
# - no extra fields allowed

from pydantic import BaseModel, Field


class Confidence(BaseModel):
    base: float = Field(..., ge=0.0, le=1.0)
    final: float = Field(..., ge=0.0, le=1.0)

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
