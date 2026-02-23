# domain/contracts/confidence.py

# Confidence contract
#
# This contract defines the structure of a confidence that can be used in the interview simulator.
# It is used to store the confidence in the database and to retrieve it when needed.
#
# The confidence is associated with a question and contains the confidence in the answer.
# The base confidence is the confidence of the model on single answer.
# The final confidence is the post-interview aggregated confidence.
#
# Responsability: represents a frozen and immutable confidence in time.

from pydantic import BaseModel, Field


class Confidence(BaseModel):
    base: float = Field(..., ge=0.0, le=1.0)
    final: float = Field(..., ge=0.0, le=1.0)

    model_config = {"frozen": True}