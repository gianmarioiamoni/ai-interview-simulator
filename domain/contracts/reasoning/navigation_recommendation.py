# domain/contracts/reasoning/navigation_recommendation.py

from pydantic import BaseModel, Field

from domain.contracts.reasoning.evidence_type import EvidenceType


class NavigationRecommendation(BaseModel):
    """Advisory navigation recommendation emitted by InterviewReasoner.

    AdaptiveNavigationNode reads this as a soft hint; it retains full
    authority over question selection (ADR-030).
    """

    suggested_area: str | None = None
    deepen_current: bool = False
    skip_area: str | None = None
    trigger_types: list[EvidenceType] = Field(default_factory=list)

    model_config = {"frozen": True, "extra": "forbid"}
