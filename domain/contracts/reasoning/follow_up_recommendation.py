# domain/contracts/reasoning/follow_up_recommendation.py

from pydantic import BaseModel, Field

from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension


class FollowUpRecommendation(BaseModel):
    """Advisory follow-up recommendation emitted by InterviewReasoner.

    `recommended=True` is a hint to question_node; question_node retains
    full authority (ADR-030). This never overrides M1 FollowUpSelector slots.
    """

    recommended: bool
    target_dimension: ProfileDimension | None = None
    trigger_types: list[EvidenceType] = Field(default_factory=list)
    # 1 = high priority, 3 = low priority
    priority: int = Field(default=2, ge=1, le=3)

    model_config = {"frozen": True, "extra": "forbid"}
