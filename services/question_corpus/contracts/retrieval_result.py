# services/question_corpus/contracts/retrieval_result.py

from pydantic import BaseModel

from langchain_core.documents import Document


class RetrievalResult(BaseModel):

    document: Document

    distance: float

    embedding: list[float]

    semantic_score: float

    quality_score: float

    model_config = {
        "arbitrary_types_allowed": True,
        "frozen": True,
    }
