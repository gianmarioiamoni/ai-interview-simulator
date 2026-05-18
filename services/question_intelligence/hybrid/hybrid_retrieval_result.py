# services/question_intelligence/hybrid/hybrid_retrieval_result.py

from pydantic import BaseModel


class HybridRetrievalResult(BaseModel):

    text: str

    semantic_score: float

    keyword_score: float

    final_score: float

    model_config = {
        "frozen": True,
    }
