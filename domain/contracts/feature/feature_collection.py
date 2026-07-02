# domain/contracts/feature/feature_collection.py
# FeatureCollection — runtime container supporting filter, order, group, compare (E01-M4)

from __future__ import annotations

from collections import defaultdict
from typing import Callable

from pydantic import BaseModel, Field

from domain.contracts.feature.feature_batch import FeatureBatch
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.profile_feature import ProfileFeature


class FeatureCollection(BaseModel):
    """Immutable, ordered container of ProfileFeatures with rich query support.

    FeatureCollection is the primary runtime surface for:
    - Filtering subsets of features.
    - Ordering by any derived key.
    - Grouping into FeatureBatch maps.
    - Lookup by FeatureType or feature_type_id.

    It does NOT produce, merge, or compose features — that is FeatureEngine's role.
    It does NOT reference CandidateProfile or Narrative.
    """

    features: tuple[ProfileFeature, ...] = Field(
        default_factory=tuple,
        description="Ordered ProfileFeatures held in this collection",
    )

    model_config = {"frozen": True, "extra": "forbid"}

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def from_iterable(cls, items: list[ProfileFeature] | tuple[ProfileFeature, ...]) -> "FeatureCollection":
        return cls(features=tuple(items))

    # ------------------------------------------------------------------
    # Basic queries
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        return len(self.features)

    @property
    def is_empty(self) -> bool:
        return len(self.features) == 0

    def feature_type_ids(self) -> frozenset[str]:
        return frozenset(f.feature_identity.feature_type_id for f in self.features)

    def get_by_type(self, feature_type: FeatureType) -> ProfileFeature | None:
        """Return the first feature matching feature_type, or None."""
        target = feature_type.value
        for f in self.features:
            if f.feature_identity.feature_type_id == target:
                return f
        return None

    def get_by_type_id(self, feature_type_id: str) -> ProfileFeature | None:
        for f in self.features:
            if f.feature_identity.feature_type_id == feature_type_id:
                return f
        return None

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter(self, predicate: Callable[[ProfileFeature], bool]) -> "FeatureCollection":
        """Return a new FeatureCollection containing only features matching predicate."""
        return FeatureCollection(features=tuple(f for f in self.features if predicate(f)))

    def filter_by_type(self, *feature_types: FeatureType) -> "FeatureCollection":
        ids = frozenset(ft.value for ft in feature_types)
        return self.filter(lambda f: f.feature_identity.feature_type_id in ids)

    def filter_by_min_confidence(self, min_confidence: float) -> "FeatureCollection":
        return self.filter(lambda f: f.quality.confidence.value >= min_confidence)

    def filter_by_maturity(self, *stages: str) -> "FeatureCollection":
        stage_set = frozenset(stages)
        return self.filter(lambda f: f.quality.maturity.stage in stage_set)

    def filter_by_stability(self, *states: str) -> "FeatureCollection":
        state_set = frozenset(states)
        return self.filter(lambda f: f.quality.stability.state in state_set)

    # ------------------------------------------------------------------
    # Ordering
    # ------------------------------------------------------------------

    def sorted_by(
        self,
        key: Callable[[ProfileFeature], object],
        descending: bool = False,
    ) -> "FeatureCollection":
        return FeatureCollection(
            features=tuple(sorted(self.features, key=key, reverse=descending))
        )

    def sorted_by_confidence(self, descending: bool = True) -> "FeatureCollection":
        return self.sorted_by(lambda f: f.quality.confidence.value, descending=descending)

    def sorted_by_type_id(self) -> "FeatureCollection":
        return self.sorted_by(lambda f: f.feature_identity.feature_type_id)

    def sorted_by_question_index(self, descending: bool = False) -> "FeatureCollection":
        return self.sorted_by(lambda f: f.computed_at_question_index, descending=descending)

    # ------------------------------------------------------------------
    # Grouping
    # ------------------------------------------------------------------

    def group_by(
        self, key_fn: Callable[[ProfileFeature], str]
    ) -> dict[str, FeatureBatch]:
        groups: dict[str, list[ProfileFeature]] = defaultdict(list)
        for f in self.features:
            groups[key_fn(f)].append(f)
        return {k: FeatureBatch(key=k, items=tuple(v)) for k, v in groups.items()}

    def group_by_type_id(self) -> dict[str, FeatureBatch]:
        return self.group_by(lambda f: f.feature_identity.feature_type_id)

    def group_by_maturity(self) -> dict[str, FeatureBatch]:
        return self.group_by(lambda f: f.quality.maturity.stage)

    def group_by_stability(self) -> dict[str, FeatureBatch]:
        return self.group_by(lambda f: f.quality.stability.state)
