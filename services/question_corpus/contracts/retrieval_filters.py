# services/question_corpus/contracts/retrieval_filters.py

from pydantic import BaseModel


class RetrievalFilters(BaseModel):

    role: str | None = None

    seniority: str | None = None

    area: str | None = None

    domains: list[str] = []

    min_difficulty: int | None = None

    max_difficulty: int | None = None

    
    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
