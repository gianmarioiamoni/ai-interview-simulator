# services/planning_validation/validation_result.py

from pydantic import BaseModel

from services.planning_validation.recovery_action import (
    RecoveryAction,
)


class ValidationResult(BaseModel):

    is_valid: bool

    violated_constraints: list[str]

    suggested_recovery_actions: list[RecoveryAction]

    model_config = {
        "frozen": True,
    }
