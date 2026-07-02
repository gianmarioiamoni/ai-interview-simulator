# domain/contracts/coaching/study_recommendation.py
# StudyRecommendation — a targeted resource or study path (ADR-025)

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from domain.contracts.coaching.learning_objective import LearningObjective


class ResourceType(str, Enum):
    """Type of recommended study resource."""

    DOCUMENTATION = "documentation"
    EXERCISE = "exercise"
    CONCEPT_REVIEW = "concept_review"
    PROJECT = "project"
    READING = "reading"


class StudyRecommendation(BaseModel):
    """A specific study resource or path mapped to a LearningObjective.

    Invariants (ADR-025):
    - Immutable.
    - Linked to one LearningObjective via objective_id.
    - No AI-generated narrative; topic and rationale are deterministic labels.
    """

    recommendation_id: str = Field(..., min_length=1)
    objective_id: str = Field(..., min_length=1)
    resource_type: ResourceType
    topic: str = Field(..., min_length=1, description="Subject area or concept to study")
    rationale: str = Field(..., min_length=1, description="Why this resource addresses the gap")
    estimated_duration_hours: float = Field(..., gt=0.0)
    tags: frozenset[str] = Field(default_factory=frozenset)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def for_objective(
        cls,
        objective: LearningObjective,
        recommendation_id: str,
        resource_type: ResourceType,
        topic: str,
        rationale: str,
        estimated_duration_hours: float,
        tags: frozenset[str] | None = None,
    ) -> "StudyRecommendation":
        return cls(
            recommendation_id=recommendation_id,
            objective_id=objective.objective_id,
            resource_type=resource_type,
            topic=topic,
            rationale=rationale,
            estimated_duration_hours=estimated_duration_hours,
            tags=tags or frozenset(),
        )
