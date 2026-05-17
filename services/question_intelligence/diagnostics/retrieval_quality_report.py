# services/question_intelligence/diagnostics/retrieval_quality_report.py

from pydantic import BaseModel


class RetrievalQualityReport(BaseModel):

    retrieved_count: int

    average_similarity: float

    max_similarity: float

    diversity_score: float

    duplicate_risk: float

    model_config = {
        "frozen": True,
    }
