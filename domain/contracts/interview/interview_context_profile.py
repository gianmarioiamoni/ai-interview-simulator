# domain/contracts/interview/interview_context_profile.py

from pydantic import BaseModel


class InterviewContextProfile(BaseModel):

    job_description: str | None = None
    company_description: str | None = None

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
