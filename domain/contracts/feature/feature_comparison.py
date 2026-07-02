# domain/contracts/feature/feature_comparison.py
# FeatureComparison — pairwise comparison of two ProfileFeatures (E01-M4)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.feature.feature_delta import DeltaDirection, FeatureDelta, FeatureDeltaSet
from domain.contracts.feature.feature_collection import FeatureCollection
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.profile_feature import ProfileFeature


class FeatureComparison(BaseModel):
    """Pairwise structural comparison of two ProfileFeatures with the same identity.

    Reports value equality, confidence ordering, quality rank, and the
    derived FeatureDelta. Does NOT modify or merge features.

    Invariants:
    - left and right must share the same feature_identity.
    - All fields are computed at construction time.
    """

    feature_identity: FeatureIdentity
    left_value: str
    right_value: str
    left_confidence: float = Field(..., ge=0.0, le=1.0)
    right_confidence: float = Field(..., ge=0.0, le=1.0)
    values_equal: bool
    left_has_higher_confidence: bool
    right_has_higher_confidence: bool
    confidence_delta: float = Field(description="right_confidence - left_confidence")
    delta: FeatureDelta

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def compare(
        cls,
        left: ProfileFeature,
        right: ProfileFeature,
        question_index: int,
    ) -> "FeatureComparison":
        if left.feature_identity != right.feature_identity:
            raise ValueError(
                f"Cannot compare features with different identities: "
                f"{left.feature_identity.feature_type_id!r} vs "
                f"{right.feature_identity.feature_type_id!r}"
            )
        lc = left.quality.confidence.value
        rc = right.quality.confidence.value
        return cls(
            feature_identity=left.feature_identity,
            left_value=left.value,
            right_value=right.value,
            left_confidence=lc,
            right_confidence=rc,
            values_equal=left.value == right.value,
            left_has_higher_confidence=lc > rc,
            right_has_higher_confidence=rc > lc,
            confidence_delta=rc - lc,
            delta=FeatureDelta.between(left, right, question_index),
        )


class FeatureCollectionComparison(BaseModel):
    """Side-by-side comparison summary of two FeatureCollections.

    Reports per-feature comparisons and aggregated delta set.
    Useful for cross-session or cross-cycle analysis.
    """

    comparisons: tuple[FeatureComparison, ...] = Field(default_factory=tuple)
    delta_set: FeatureDeltaSet
    shared_type_ids: frozenset[str] = Field(default_factory=frozenset)
    left_only_type_ids: frozenset[str] = Field(default_factory=frozenset)
    right_only_type_ids: frozenset[str] = Field(default_factory=frozenset)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def compare(
        cls,
        left: FeatureCollection,
        right: FeatureCollection,
        question_index: int,
    ) -> "FeatureCollectionComparison":
        left_map = {f.feature_identity.feature_type_id: f for f in left.features}
        right_map = {f.feature_identity.feature_type_id: f for f in right.features}

        shared = frozenset(left_map) & frozenset(right_map)
        comparisons = tuple(
            FeatureComparison.compare(left_map[k], right_map[k], question_index)
            for k in sorted(shared)
        )
        return cls(
            comparisons=comparisons,
            delta_set=FeatureDeltaSet.compute(left, right, question_index),
            shared_type_ids=shared,
            left_only_type_ids=frozenset(left_map) - frozenset(right_map),
            right_only_type_ids=frozenset(right_map) - frozenset(left_map),
        )

    @property
    def improved(self) -> tuple[FeatureComparison, ...]:
        return tuple(
            c for c in self.comparisons if c.delta.direction == DeltaDirection.IMPROVED
        )

    @property
    def degraded(self) -> tuple[FeatureComparison, ...]:
        return tuple(
            c for c in self.comparisons if c.delta.direction == DeltaDirection.DEGRADED
        )
