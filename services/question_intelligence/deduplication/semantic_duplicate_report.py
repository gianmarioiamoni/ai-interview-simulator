# services/question_intelligence/deduplication/semantic_duplicate_report.py

from pydantic import BaseModel

from typing import List


class DuplicatePair(BaseModel):

    left: str

    right: str

    similarity: float


class SemanticDuplicateReport(BaseModel):

    total_documents: int

    duplicate_pairs: List[DuplicatePair]

    duplicate_ratio: float

    max_similarity: float

    model_config = {
        "frozen": True,
    }
