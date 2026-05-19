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

from services.planning_validation.validation_result import (
    ValidationResult,
)


class OrchestrationResult(BaseModel):

    candidate_pool: CandidatePool

    planning_result: PlanningResult

    assembly_result: AdaptiveInterviewResult

    validation_result: ValidationResult

    model_config = {
        "frozen": True,
    }
