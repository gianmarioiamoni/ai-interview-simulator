# domain/contracts/feedback/decision_explanation_schema.py

from pydantic import BaseModel, Field
from typing import List


class DecisionExplanationSchema(BaseModel):
    drivers: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
