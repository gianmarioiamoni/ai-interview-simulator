# services/interview_planning/planning_result.py

from pydantic import BaseModel

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)


class PlanningResult(BaseModel):

    selected_questions: list[QuestionBankItem]

    satisfied_constraints: list[str]

    violated_constraints: list[str]

    average_difficulty: float

    model_config = {
        "frozen": True,
    }
