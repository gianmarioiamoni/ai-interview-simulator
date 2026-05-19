# services/interview_selection/interview_selection_result.py

from pydantic import BaseModel

from services.interview_selection.selected_question import (
    SelectedQuestion,
)


class InterviewSelectionResult(BaseModel):

    selected_questions: list[SelectedQuestion]

    total_questions: int

    coverage_score: float

    average_difficulty: float

    model_config = {
        "frozen": True,
    }
