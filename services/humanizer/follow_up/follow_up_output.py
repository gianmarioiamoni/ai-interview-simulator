# services/humanizer/follow_up/follow_up_output.py

from pydantic import BaseModel, Field, field_validator


class FollowUpOutput(BaseModel):
    """DTO for the LLM-generated follow-up question response.

    Strict schema: no extra fields allowed, all fields required.
    confidence must be in [0.0, 1.0].
    """

    follow_up_question: str = Field(..., min_length=1)
    reasoning: str = Field(..., min_length=1)
    topic_anchor: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }

    @field_validator("follow_up_question")
    @classmethod
    def must_contain_question_mark(cls, v: str) -> str:
        if "?" not in v:
            raise ValueError("follow_up_question must contain a question mark")
        return v
