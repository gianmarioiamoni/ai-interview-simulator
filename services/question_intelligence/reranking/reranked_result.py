# services/question_intelligence/reranking/reranked_result.py

from pydantic import BaseModel

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)


class RerankedResult(BaseModel):

    item: QuestionBankItem

    semantic_score: float

    redundancy_penalty: float

    final_score: float

    model_config = {
        "frozen": True,
    }
