# services/question_intelligence/retrieval/retrieval_strategy.py

from pydantic import BaseModel


class RetrievalStrategy(BaseModel):

    k: int

    fetch_k: int

    use_mmr: bool = True

    lambda_mult: float = 0.5
