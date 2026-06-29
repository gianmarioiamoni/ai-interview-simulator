# services/humanizer/follow_up/follow_up_prompt_input.py

from pydantic import BaseModel, Field


class FollowUpPromptInput(BaseModel):
    """Input contract for the follow-up prompt builder."""

    question_area: str = Field(..., min_length=1)
    previous_question: str = Field(..., min_length=1)
    previous_answer: str = Field(..., min_length=1)
    previous_feedback: str = ""
    candidate_level: str = ""
    role: str = ""
    seniority: str = ""
    job_description: str = ""
    company_description: str = ""
    business_context: str = ""
    follow_up_type: str = "deep_dive"

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
