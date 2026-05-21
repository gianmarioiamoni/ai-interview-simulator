# services/interview_selection/selected_question.py

from pydantic import BaseModel

from domain.contracts.question.question_bank_item import QuestionBankItem

from services.planning.contracts.planner_score_breakdown import PlannerScoreBreakdown


class SelectedQuestion(BaseModel):

    item: QuestionBankItem

    selection_score: float

    score_breakdown: PlannerScoreBreakdown

    selection_reason: str

    model_config = {
        "frozen": True,
    }
