# app/ui/dto/question_dto.py

from dataclasses import dataclass

from domain.contracts.question import QuestionType


@dataclass
class QuestionDTO:
    question_id: str
    text: str
    type: QuestionType
    area: str
    index: int
    total: int
