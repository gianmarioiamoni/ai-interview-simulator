# services/interview_selection/assembled_question.py

from pydantic import BaseModel

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.interview_selection.interview_stage import (
    InterviewStage,
)

from services.planning.contracts.planner_score_breakdown import PlannerScoreBreakdown


class AssembledQuestion(BaseModel):

    item: QuestionBankItem

    stage: InterviewStage

    assembly_reason: str

    score_breakdown: PlannerScoreBreakdown

    model_config = {
        "frozen": True,
    }
