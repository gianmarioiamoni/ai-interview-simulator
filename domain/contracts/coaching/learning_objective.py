# domain/contracts/coaching/learning_objective.py
# LearningObjective — targeted skill gap identified during interview (ADR-025)

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.observation.observation_type import ObservationType


class ObjectivePriority(str, Enum):
    """Urgency/importance tier for a LearningObjective."""

    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class LearningObjective(BaseModel):
    """A specific, observable skill gap identified from ProfileFeatures and Observations.

    Invariants (ADR-025):
    - Immutable after construction.
    - Derived purely from runtime evidence; no narrative generation.
    - feature_type identifies the affected knowledge axis.
    - supporting_observation_types record the evidence basis.
    """

    objective_id: str = Field(..., min_length=1, description="Stable, unique identifier")
    feature_type: FeatureType = Field(..., description="Knowledge axis this objective targets")
    description: str = Field(..., min_length=1, description="Concise, actionable gap description")
    priority: ObjectivePriority = Field(default=ObjectivePriority.MODERATE)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Evidence strength [0,1]")
    supporting_observation_types: tuple[ObservationType, ...] = Field(
        default_factory=tuple,
        description="ObservationTypes that contributed to this objective",
    )
    detected_at_question_index: int = Field(..., ge=0)
    candidate_identity_id: str = Field(..., min_length=1)

    model_config = {"frozen": True, "extra": "forbid"}
