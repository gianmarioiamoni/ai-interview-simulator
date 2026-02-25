# app/ui/dto/question_assessment_dto.py

from dataclasses import dataclass


@dataclass
class QuestionAssessmentDTO:
    question_id: str
    score: float
    feedback: str
