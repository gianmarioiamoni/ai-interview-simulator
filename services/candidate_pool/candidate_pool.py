# services/candidate_pool/candidate_pool.py

from pydantic import BaseModel

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)


class CandidatePool(BaseModel):

    eligible_questions: list[QuestionBankItem]

    rejected_questions: list[QuestionBankItem]

    total_candidates: int

    eligible_count: int

    rejected_count: int

    model_config = {
        "frozen": True,
    }
