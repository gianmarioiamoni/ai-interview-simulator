# app/ui/dto/question_dto.py

from dataclasses import dataclass
from typing import Literal


QuestionType = Literal["written", "coding", "database"]


@dataclass
class QuestionDTO:
    question_id: str
    text: str
    question_type: QuestionType
    area: str
    index: int
    total: int
