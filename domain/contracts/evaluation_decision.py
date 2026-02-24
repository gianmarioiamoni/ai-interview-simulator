# domain/contracts/evaluation_decision.py

from pydantic import BaseModel, Field
from typing import Optional


class EvaluationDecision(BaseModel):
    score: float = Field(ge=0.0, le=100.0)
    feedback: str = Field(min_length=1)
    clarification_needed: bool
    follow_up_question: Optional[str] = None
