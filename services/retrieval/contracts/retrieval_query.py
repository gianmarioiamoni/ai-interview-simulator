# services/retrieval/contracts/retrieval_query.py

from pydantic import BaseModel


class RetrievalQuery(BaseModel):

    text: str

    required_tags: list[str] = []

    preferred_categories: list[str] = []

    minimum_score: float = 0.0

    top_k: int = 5

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
