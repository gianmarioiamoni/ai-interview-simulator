# services/interview_planning/planning_result.py

from pydantic import BaseModel

from services.interview_selection.selected_question import SelectedQuestion
from services.interview_planning.contracts.planning_artifacts import PlanningArtifacts


class PlanningResult(BaseModel):

    selected_questions: list[SelectedQuestion]

    satisfied_constraints: list[str]

    violated_constraints: list[str]

    average_difficulty: float

    artifacts: PlanningArtifacts

    model_config = {
        "frozen": True,
    }
