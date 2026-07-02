# domain/contracts/feature/feature_ordering.py
# FeatureOrdering — composable sort-key factory for FeatureCollection (E01-M4)

from __future__ import annotations

from typing import Callable

from domain.contracts.feature.feature_quality import (
    MATURITY_MATURE,
    MATURITY_DEVELOPING,
    MATURITY_NASCENT,
    STABILITY_STABLE,
    STABILITY_UNSTABLE,
    STABILITY_EMERGING,
)
from domain.contracts.feature.profile_feature import ProfileFeature


# Type alias for a sort key extractor
FeatureSortKey = Callable[[ProfileFeature], object]

_MATURITY_RANK: dict[str, int] = {
    MATURITY_NASCENT: 0,
    MATURITY_DEVELOPING: 1,
    MATURITY_MATURE: 2,
}
_STABILITY_RANK: dict[str, int] = {
    STABILITY_EMERGING: 0,
    STABILITY_UNSTABLE: 1,
    STABILITY_STABLE: 2,
}


class FeatureOrdering:
    """Stateless sort-key factory for ProfileFeature ordering.

    All methods return callables suitable for sorted() or FeatureCollection.sorted_by().
    Methods prefixed with `desc_` return negated numeric keys for descending order.
    """

    @staticmethod
    def by_confidence_asc() -> FeatureSortKey:
        return lambda f: f.quality.confidence.value

    @staticmethod
    def by_confidence_desc() -> FeatureSortKey:
        return lambda f: -f.quality.confidence.value

    @staticmethod
    def by_type_id_asc() -> FeatureSortKey:
        return lambda f: f.feature_identity.feature_type_id

    @staticmethod
    def by_maturity_asc() -> FeatureSortKey:
        return lambda f: _MATURITY_RANK.get(f.quality.maturity.stage, -1)

    @staticmethod
    def by_maturity_desc() -> FeatureSortKey:
        return lambda f: -_MATURITY_RANK.get(f.quality.maturity.stage, -1)

    @staticmethod
    def by_stability_asc() -> FeatureSortKey:
        return lambda f: _STABILITY_RANK.get(f.quality.stability.state, -1)

    @staticmethod
    def by_stability_desc() -> FeatureSortKey:
        return lambda f: -_STABILITY_RANK.get(f.quality.stability.state, -1)

    @staticmethod
    def by_question_index_asc() -> FeatureSortKey:
        return lambda f: f.computed_at_question_index

    @staticmethod
    def by_question_index_desc() -> FeatureSortKey:
        return lambda f: -f.computed_at_question_index

    @staticmethod
    def by_observation_count_asc() -> FeatureSortKey:
        return lambda f: f.quality.maturity.observation_count

    @staticmethod
    def by_observation_count_desc() -> FeatureSortKey:
        return lambda f: -f.quality.maturity.observation_count

    @staticmethod
    def composite(*keys: FeatureSortKey) -> FeatureSortKey:
        """Combine multiple sort keys into a tuple-based composite key."""
        return lambda f: tuple(k(f) for k in keys)
