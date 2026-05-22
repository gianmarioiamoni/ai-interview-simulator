# services/interview_planning/contracts/planning_artifacts.py

from pydantic import BaseModel

from services.telemetry.planner.planner_telemetry import (
    PlannerTelemetry,
)


class PlanningArtifacts(BaseModel):

    telemetry: PlannerTelemetry

    planner_version: str

    optimization_strategy: str

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
