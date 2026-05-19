# services/interview_selection/selected_question.py

from pydantic import BaseModel

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)


class SelectedQuestion(BaseModel):

    item: QuestionBankItem

    selection_score: float

    selection_reason: str

    model_config = {
        "frozen": True,
    }
