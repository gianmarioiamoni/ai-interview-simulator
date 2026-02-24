# domain/contracts/evaluation_decision.py

from pydantic import BaseModel, Field, model_validator
from typing import Optional


class EvaluationDecision(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0)
    feedback: str = Field(..., min_length=1)
    clarification_needed: bool
    follow_up_question: Optional[str] = None

    model_config = {
        "extra": "forbid",
    }

    @model_validator(mode="after")
    def validate_consistency(self) -> "EvaluationDecision":

        if self.clarification_needed and not self.follow_up_question:
            raise ValueError(
                "Follow-up question required when clarification_needed is True"
            )

        if not self.clarification_needed and self.follow_up_question:
            raise ValueError(
                "Follow-up question must be None when clarification_needed is False"
            )

        return self
