from pydantic import BaseModel

from services.interview_selection.interview_stage import (
    InterviewStage,
)


class QuestionRuntimeLineage(BaseModel):

    selection_score: float | None = None

    selection_reason: str | None = None

    assembly_reason: str | None = None

    interview_stage: InterviewStage | None = None

    planner_rationale: list[str] = []

    recovery_applied: bool = False

    
    model_config = {
        "frozen": True,
    }
