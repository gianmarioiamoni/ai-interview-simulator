# app/ui/dto/interview_session_dto.py

from dataclasses import dataclass
from typing import Optional

from app.ui.dto.question_dto import QuestionDTO


@dataclass
class InterviewSessionDTO:
    session_id: str
    current_question: Optional[QuestionDTO]
    is_completed: bool
    current_area: Optional[str]
