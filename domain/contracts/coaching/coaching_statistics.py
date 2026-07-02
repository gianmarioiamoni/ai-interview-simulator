# domain/contracts/coaching/coaching_statistics.py
# CoachingStatistics — aggregate metrics over a CoachingCollection (ADR-025)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.coaching.coaching_collection import CoachingCollection
from domain.contracts.coaching.learning_objective import ObjectivePriority


class CoachingStatistics(BaseModel):
    """Descriptive metrics derived from a CoachingCollection.

    Computed once; immutable. Mirrors FeatureStatistics / ObservationStatistics pattern.

    Invariants (ADR-025):
    - All counts are non-negative.
    - mean_objective_confidence is 0.0 when no objectives exist.
    - priority_counts keys cover all ObjectivePriority values present in the collection.
    """

    total_objectives: int = Field(..., ge=0)
    total_actions: int = Field(..., ge=0)
    total_recommendations: int = Field(..., ge=0)
    immediate_action_count: int = Field(..., ge=0)
    mean_objective_confidence: float = Field(..., ge=0.0, le=1.0)
    min_objective_confidence: float = Field(..., ge=0.0, le=1.0)
    max_objective_confidence: float = Field(..., ge=0.0, le=1.0)
    critical_objective_count: int = Field(..., ge=0)
    high_objective_count: int = Field(..., ge=0)
    moderate_objective_count: int = Field(..., ge=0)
    low_objective_count: int = Field(..., ge=0)
    distinct_feature_type_count: int = Field(..., ge=0)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_collection(cls, collection: CoachingCollection) -> "CoachingStatistics":
        objectives = collection.objectives
        actions = collection.actions

        if not objectives:
            return cls(
                total_objectives=0,
                total_actions=len(actions),
                total_recommendations=len(collection.recommendations),
                immediate_action_count=sum(1 for a in actions if a.is_immediate),
                mean_objective_confidence=0.0,
                min_objective_confidence=0.0,
                max_objective_confidence=0.0,
                critical_objective_count=0,
                high_objective_count=0,
                moderate_objective_count=0,
                low_objective_count=0,
                distinct_feature_type_count=0,
            )

        confidences = [o.confidence for o in objectives]
        return cls(
            total_objectives=len(objectives),
            total_actions=len(actions),
            total_recommendations=len(collection.recommendations),
            immediate_action_count=sum(1 for a in actions if a.is_immediate),
            mean_objective_confidence=sum(confidences) / len(confidences),
            min_objective_confidence=min(confidences),
            max_objective_confidence=max(confidences),
            critical_objective_count=sum(
                1 for o in objectives if o.priority == ObjectivePriority.CRITICAL
            ),
            high_objective_count=sum(
                1 for o in objectives if o.priority == ObjectivePriority.HIGH
            ),
            moderate_objective_count=sum(
                1 for o in objectives if o.priority == ObjectivePriority.MODERATE
            ),
            low_objective_count=sum(
                1 for o in objectives if o.priority == ObjectivePriority.LOW
            ),
            distinct_feature_type_count=len({o.feature_type for o in objectives}),
        )

    @property
    def priority_distribution(self) -> dict[str, int]:
        return {
            ObjectivePriority.CRITICAL.value: self.critical_objective_count,
            ObjectivePriority.HIGH.value: self.high_objective_count,
            ObjectivePriority.MODERATE.value: self.moderate_objective_count,
            ObjectivePriority.LOW.value: self.low_objective_count,
        }

    @property
    def is_empty(self) -> bool:
        return self.total_objectives == 0
