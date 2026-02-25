# app/ui/dto/final_report_dto.py

from dataclasses import dataclass
from typing import List
from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from app.ui.dto.question_assessment_dto import QuestionAssessmentDTO


@dataclass
class FinalReportDTO:
    overall_score: float
    hiring_probability: float
    dimension_scores: List[DimensionScoreDTO]
    question_assessments: List[QuestionAssessmentDTO]
    improvement_suggestions: List[str]
    total_tokens_used: int
