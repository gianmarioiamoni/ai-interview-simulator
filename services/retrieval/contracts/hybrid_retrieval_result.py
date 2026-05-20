# services/retrieval/contracts/hybrid_retrieval_result.py

from pydantic import BaseModel

from services.retrieval.contracts import (
    RetrievalResult,
)


class HybridRetrievalResult(BaseModel):

    symbolic_result: RetrievalResult

    embedding_similarity: float

    fused_score: float

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
