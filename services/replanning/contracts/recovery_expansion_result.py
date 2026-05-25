# services/replanning/contracts/recovery_expansion_result.py

from pydantic import BaseModel

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.planning_validation.recovery_action import (
    RecoveryAction,
)


class RecoveryExpansionResult(BaseModel):

    expanded_items: list[QuestionBankItem]

    applied_action: RecoveryAction

    added_candidates: int

    model_config = {
        "frozen": True,
    }
