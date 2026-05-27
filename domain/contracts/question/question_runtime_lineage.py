# domain/contracts/question/question_runtime_lineage.py

from pydantic import BaseModel, Field

from services.interview_selection.interview_stage import (
    InterviewStage,
)


class QuestionRuntimeLineage(BaseModel):

    selection_score: float | None = None

    selection_reason: str | None = None

    assembly_reason: str | None = None

    interview_stage: InterviewStage | None = None

    planner_rationale: list[str] = Field(default_factory=list)

    recovery_applied: bool = False

    
    model_config = {
        "frozen": True,
    }
