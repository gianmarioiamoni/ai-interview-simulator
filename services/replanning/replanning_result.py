# services/replanning/replanning_result.py

from pydantic import BaseModel

from services.interview_planning.planning_result import PlanningResult
from services.planning_validation.validation_result import ValidationResult
from services.planning_validation.recovery_action import RecoveryAction


class ReplanningResult(BaseModel):

    final_planning_result: PlanningResult

    final_validation_result: ValidationResult

    applied_recovery_actions: list[RecoveryAction]

    total_attempts: int

    model_config = {
        "frozen": True,
    }
