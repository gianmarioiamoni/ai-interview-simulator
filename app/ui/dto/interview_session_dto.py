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

    @classmethod
    def from_state(cls, state):

        question = state.current_question

        question_dto = None
        current_area = None

        if question is not None:

            index = state.current_question_index + 1
            total = len(state.questions)

            question_dto = QuestionDTO(
                question_id=question.id,
                text=question.prompt,
                question_type=question.type.value,
                area=question.area.value,
                index=index,
                total=total,
            )

            current_area = question.area.value

        return cls(
            session_id=state.interview_id,
            current_question=question_dto,
            is_completed=state.progress.value == "completed",
            current_area=current_area,
        )
