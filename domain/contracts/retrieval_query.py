# domain/contracts/retrieval_query.py

from pydantic import BaseModel, Field


class RetrievalQuery(BaseModel):
    query: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    company: str = Field(..., min_length=1)
    area: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)

    model_config = {"frozen": True}
