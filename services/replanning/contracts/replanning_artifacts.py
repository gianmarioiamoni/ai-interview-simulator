# services/replanning/contracts/replanning_artifacts.py

from pydantic import BaseModel

from services.telemetry.planner.planner_telemetry import PlannerTelemetry
from services.replanning.contracts.retrieval_expansion_telemetry import RetrievalExpansionTelemetry
from services.planning_validation.recovery_action import RecoveryAction


class ReplanningArtifacts(BaseModel):

    planner_telemetry: PlannerTelemetry

    retrieval_expansion_telemetry: RetrievalExpansionTelemetry | None = None

    recovery_attempts: int

    applied_actions: list[RecoveryAction]

    model_config = {
        "frozen": True,
    }
