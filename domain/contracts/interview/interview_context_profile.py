# domain/contracts/interview/interview_context_profile.py

from pydantic import BaseModel

from domain.contracts.interview.business_context import BusinessContext


class InterviewContextProfile(BaseModel):

    job_description: str | None = None
    company_description: str | None = None
    business_context: BusinessContext = BusinessContext.GENERIC

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
