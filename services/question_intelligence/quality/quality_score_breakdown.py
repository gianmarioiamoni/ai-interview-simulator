# services/question_intelligence/quality/quality_score_breakdown.py

from pydantic import BaseModel


class QualityScoreBreakdown(BaseModel):

    practical_relevance: float

    production_relevance: float

    architectural_depth: float

    ambiguity_penalty: float

    seniority_alignment: float

    final_score: float

    model_config = {
        "frozen": True,
    }
