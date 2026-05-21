# services/interview_planning/planning_result.py

from pydantic import BaseModel

from services.interview_selection.selected_question import SelectedQuestion
from services.planning.contracts.planner_telemetry import PlannerTelemetry


class PlanningResult(BaseModel):

    selected_questions: list[SelectedQuestion]

    satisfied_constraints: list[str]

    violated_constraints: list[str]

    average_difficulty: float

    telemetry: PlannerTelemetry

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
