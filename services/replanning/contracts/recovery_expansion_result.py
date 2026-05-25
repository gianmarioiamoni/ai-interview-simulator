# services/replanning/contracts/recovery_expansion_result.py

from pydantic import BaseModel

from domain.contracts.question.question_bank_item import QuestionBankItem

from services.replanning.contracts.retrieval_expansion_telemetry import RetrievalExpansionTelemetry
from services.planning_validation.recovery_action import RecoveryAction


class RecoveryExpansionResult(BaseModel):

    expanded_items: list[QuestionBankItem]

    applied_action: RecoveryAction

    added_candidates: int

    telemetry: RetrievalExpansionTelemetry | None = None

    model_config = {
        "frozen": True,
    }
