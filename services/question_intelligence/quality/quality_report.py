# services/question_intelligence/quality/quality_report.py

from pydantic import BaseModel


class QualityReport(BaseModel):

    average_similarity: float

    max_similarity: float

    duplicate_pairs: int

    diversity_score: float
