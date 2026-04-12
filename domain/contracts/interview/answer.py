# domain/contracts/answer.py

from pydantic import BaseModel, Field


class Answer(BaseModel):
    question_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)

    # useful for follow-up tracking
    attempt: int = Field(..., ge=1)

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
