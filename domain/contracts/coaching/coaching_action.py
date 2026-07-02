# domain/contracts/coaching/coaching_action.py
# CoachingAction — a concrete, prioritised remediation step (ADR-025)

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from domain.contracts.coaching.learning_objective import LearningObjective


class ActionCategory(str, Enum):
    """Broad category of a coaching action."""

    PRACTICE = "practice"
    REVIEW = "review"
    DEEP_DIVE = "deep_dive"
    REFLECTION = "reflection"
    EXPOSURE = "exposure"


class CoachingAction(BaseModel):
    """Concrete, prioritised step to address a LearningObjective.

    Invariants (ADR-025):
    - Immutable.
    - Always linked to exactly one LearningObjective via objective_id.
    - No narrative text generation; description is a factual directive.
    - effort_estimate_hours must be positive.
    """

    action_id: str = Field(..., min_length=1)
    objective_id: str = Field(..., min_length=1, description="Parent LearningObjective.objective_id")
    category: ActionCategory
    description: str = Field(..., min_length=1)
    effort_estimate_hours: float = Field(..., gt=0.0, description="Estimated effort in hours")
    is_immediate: bool = Field(
        default=False, description="True if this action should be taken before the next session"
    )
    tags: frozenset[str] = Field(default_factory=frozenset, description="Topic/skill tags")

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def for_objective(
        cls,
        objective: LearningObjective,
        action_id: str,
        category: ActionCategory,
        description: str,
        effort_estimate_hours: float,
        is_immediate: bool = False,
        tags: frozenset[str] | None = None,
    ) -> "CoachingAction":
        return cls(
            action_id=action_id,
            objective_id=objective.objective_id,
            category=category,
            description=description,
            effort_estimate_hours=effort_estimate_hours,
            is_immediate=is_immediate,
            tags=tags or frozenset(),
        )
