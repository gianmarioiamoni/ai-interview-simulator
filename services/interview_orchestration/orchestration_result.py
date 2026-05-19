# services/interview_orchestration/orchestration_result.py

from pydantic import BaseModel

from services.candidate_pool.candidate_pool import (
    CandidatePool,
)

from services.interview_planning.planning_result import (
    PlanningResult,
)

from services.interview_selection.adaptive_interview_result import (
    AdaptiveInterviewResult,
)


class OrchestrationResult(BaseModel):

    candidate_pool: CandidatePool

    planning_result: PlanningResult

    assembly_result: AdaptiveInterviewResult

    model_config = {
        "frozen": True,
    }
