# services/replanning/contracts/replanning_context.py

from pydantic import BaseModel

from domain.contracts.question.question_bank_item import QuestionBankItem

from services.interview_planning.interview_constraints import InterviewConstraints
from services.interview_planning.planning_result import PlanningResult
from services.planning_validation.validation_result import ValidationResult
from services.planning_validation.recovery_action import RecoveryAction
from services.replanning.contracts.retrieval_expansion_telemetry import RetrievalExpansionTelemetry


class ReplanningContext(BaseModel):

    items: list[QuestionBankItem]

    constraints: InterviewConstraints

    applied_actions: list[RecoveryAction] = []

    planning_history: list[PlanningResult] = []

    validation_history: list[ValidationResult] = []

    latest_expansion_telemetry: RetrievalExpansionTelemetry | None = None

    current_attempt: int = 0

    model_config = {
        "arbitrary_types_allowed": True,
    }
