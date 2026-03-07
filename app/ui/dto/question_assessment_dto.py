# app/ui/dto/question_assessment_dto.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class QuestionAssessmentDTO:
    question_id: str
    score: float
    feedback: str
    passed_tests: Optional[int]
    total_tests: Optional[int]
    execution_status: Optional[str]