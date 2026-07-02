# domain/contracts/feature/feature_delta.py
# FeatureDelta — value/confidence change between two ProfileFeature snapshots (E01-M4)

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_collection import FeatureCollection
from domain.contracts.feature.profile_feature import ProfileFeature


class DeltaDirection(str, Enum):
    """Direction of change for a feature value or confidence."""

    IMPROVED = "improved"
    DEGRADED = "degraded"
    UNCHANGED = "unchanged"
    ADDED = "added"
    REMOVED = "removed"


class FeatureDelta(BaseModel):
    """Change record between two consecutive ProfileFeature snapshots.

    Captures value change, confidence delta, and direction for one feature.
    Computed from two FeatureCollections (before → after).

    Invariants:
    - confidence_delta = after_confidence - before_confidence (may be negative).
    - value_changed is True when candidate_value strings differ.
    - direction reflects the net change from a knowledge quality perspective.
    """

    feature_identity: FeatureIdentity
    before_value: str | None = Field(default=None, description="Value before; None if ADDED")
    after_value: str | None = Field(default=None, description="Value after; None if REMOVED")
    before_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    after_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_delta: float = Field(
        default=0.0, description="after_confidence - before_confidence"
    )
    value_changed: bool = Field(default=False)
    direction: DeltaDirection = Field(default=DeltaDirection.UNCHANGED)
    computed_at_question_index: int = Field(
        ..., ge=0, description="Question index of the 'after' snapshot"
    )

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def between(
        cls,
        before: ProfileFeature | None,
        after: ProfileFeature | None,
        question_index: int,
    ) -> "FeatureDelta":
        if before is None and after is not None:
            return cls(
                feature_identity=after.feature_identity,
                before_value=None,
                after_value=after.value,
                before_confidence=None,
                after_confidence=after.quality.confidence.value,
                confidence_delta=after.quality.confidence.value,
                value_changed=True,
                direction=DeltaDirection.ADDED,
                computed_at_question_index=question_index,
            )
        if before is not None and after is None:
            return cls(
                feature_identity=before.feature_identity,
                before_value=before.value,
                after_value=None,
                before_confidence=before.quality.confidence.value,
                after_confidence=None,
                confidence_delta=-before.quality.confidence.value,
                value_changed=True,
                direction=DeltaDirection.REMOVED,
                computed_at_question_index=question_index,
            )
        if before is not None and after is not None:
            conf_delta = after.quality.confidence.value - before.quality.confidence.value
            value_changed = before.value != after.value
            if conf_delta > 0.0 or (value_changed and conf_delta >= 0.0):
                direction = DeltaDirection.IMPROVED
            elif conf_delta < 0.0:
                direction = DeltaDirection.DEGRADED
            else:
                direction = DeltaDirection.UNCHANGED
            return cls(
                feature_identity=after.feature_identity,
                before_value=before.value,
                after_value=after.value,
                before_confidence=before.quality.confidence.value,
                after_confidence=after.quality.confidence.value,
                confidence_delta=conf_delta,
                value_changed=value_changed,
                direction=direction,
                computed_at_question_index=question_index,
            )
        raise ValueError("Both before and after cannot be None")


class FeatureDeltaSet(BaseModel):
    """Complete set of FeatureDeltas between two FeatureCollection snapshots.

    Produced by FeatureDeltaSet.compute(before, after).
    """

    deltas: tuple[FeatureDelta, ...] = Field(default_factory=tuple)
    question_index: int = Field(..., ge=0)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def compute(
        cls,
        before: FeatureCollection,
        after: FeatureCollection,
        question_index: int,
    ) -> "FeatureDeltaSet":
        before_map = {f.feature_identity.feature_type_id: f for f in before.features}
        after_map = {f.feature_identity.feature_type_id: f for f in after.features}
        all_keys = set(before_map) | set(after_map)
        deltas = tuple(
            FeatureDelta.between(before_map.get(k), after_map.get(k), question_index)
            for k in sorted(all_keys)
        )
        return cls(deltas=deltas, question_index=question_index)

    def by_direction(self, direction: DeltaDirection) -> tuple[FeatureDelta, ...]:
        return tuple(d for d in self.deltas if d.direction == direction)

    @property
    def changed(self) -> tuple[FeatureDelta, ...]:
        return tuple(d for d in self.deltas if d.direction != DeltaDirection.UNCHANGED)
