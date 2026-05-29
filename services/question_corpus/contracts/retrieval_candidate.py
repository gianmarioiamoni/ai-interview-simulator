# services/question_corpus/contracts/retrieval_candidate.py

from pydantic import BaseModel

from langchain_core.documents import Document


class RetrievalCandidate(BaseModel):

    document: Document

    semantic_score: float

    quality_score: float

    final_score: float

    diversity_score: float = 0.0

    adaptive_score: float | None = None


    model_config = {
        "arbitrary_types_allowed": True,
        "frozen": True,
    }
