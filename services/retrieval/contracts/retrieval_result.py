# services/retrieval/contracts/retrieval_result.py

from pydantic import BaseModel

from services.retrieval.contracts import (
    RetrievalCorpusRecord,
)


class RetrievalResult(BaseModel):

    record: RetrievalCorpusRecord

    final_score: float

    matched_tags: list[str]

    matched_categories: list[str]

    semantic_overlap: float

    is_admissible: bool

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
