# services/question_intelligence/quality/contracts/similarity_metrics.py

from pydantic import BaseModel


class SimilarityMetrics(BaseModel):

    average_similarity: float
    max_similarity: float
    duplicate_pairs: int
