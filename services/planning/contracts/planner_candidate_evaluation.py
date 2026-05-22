# services/planning/contracts/planner_candidate_evaluation.py

from pydantic import BaseModel

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.planning.contracts.planner_score_breakdown import (
    PlannerScoreBreakdown,
)


class PlannerCandidateEvaluation(BaseModel):

    candidate: QuestionBankItem

    breakdown: PlannerScoreBreakdown

    final_score: float

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
