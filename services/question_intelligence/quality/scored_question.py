# services/question_intelligence/quality/scored_question.py

from pydantic import BaseModel

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.question_intelligence.quality.quality_score_breakdown import (
    QualityScoreBreakdown,
)


class ScoredQuestion(BaseModel):

    item: QuestionBankItem

    breakdown: QualityScoreBreakdown

    model_config = {
        "frozen": True,
    }
