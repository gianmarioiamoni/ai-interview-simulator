# domain/contracts/retrieval_query.py

from pydantic import BaseModel, Field

from domain.contracts.role import Role
from domain.contracts.interview_area import InterviewArea


class RetrievalQuery(BaseModel):
    query: str = Field(..., min_length=1)
    role: Role
    company: str = Field(..., min_length=1)
    area: InterviewArea
    top_k: int = Field(default=5, ge=1, le=20)

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
