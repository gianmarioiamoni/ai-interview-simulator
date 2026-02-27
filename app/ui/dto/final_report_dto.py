# app/ui/dto/final_report_dto.py

from pydantic import BaseModel
from typing import List
from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from app.ui.dto.question_assessment_dto import QuestionAssessmentDTO


class FinalReportDTO(BaseModel):
    overall_score: float
    hiring_probability: float
    percentile_rank: float
    executive_summary: str
    dimension_scores: List[DimensionScoreDTO]
    question_assessments: List[QuestionAssessmentDTO]
    improvement_suggestions: List[str]
    total_tokens_used: int
