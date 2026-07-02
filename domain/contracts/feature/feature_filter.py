# domain/contracts/feature/feature_filter.py
# FeatureFilter — composable predicate objects for FeatureCollection (E01-M4)

from __future__ import annotations

from typing import Callable

from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.profile_feature import ProfileFeature


# Type alias for a single predicate
FeaturePredicate = Callable[[ProfileFeature], bool]


class FeatureFilter:
    """Composable, stateless feature predicate factory.

    All methods return plain callables (FeaturePredicate) so they compose
    naturally with FeatureCollection.filter() and Python builtins.

    No state; all methods are static or class-level factory methods.
    """

    @staticmethod
    def by_type(*feature_types: FeatureType) -> FeaturePredicate:
        ids = frozenset(ft.value for ft in feature_types)
        return lambda f: f.feature_identity.feature_type_id in ids

    @staticmethod
    def by_type_id(*type_ids: str) -> FeaturePredicate:
        ids = frozenset(type_ids)
        return lambda f: f.feature_identity.feature_type_id in ids

    @staticmethod
    def min_confidence(threshold: float) -> FeaturePredicate:
        return lambda f: f.quality.confidence.value >= threshold

    @staticmethod
    def max_confidence(threshold: float) -> FeaturePredicate:
        return lambda f: f.quality.confidence.value <= threshold

    @staticmethod
    def by_maturity(*stages: str) -> FeaturePredicate:
        stage_set = frozenset(stages)
        return lambda f: f.quality.maturity.stage in stage_set

    @staticmethod
    def by_stability(*states: str) -> FeaturePredicate:
        state_set = frozenset(states)
        return lambda f: f.quality.stability.state in state_set

    @staticmethod
    def by_value(*values: str) -> FeaturePredicate:
        value_set = frozenset(values)
        return lambda f: f.value in value_set

    @staticmethod
    def at_question_index(index: int) -> FeaturePredicate:
        return lambda f: f.computed_at_question_index == index

    @staticmethod
    def after_question_index(index: int) -> FeaturePredicate:
        return lambda f: f.computed_at_question_index > index

    @staticmethod
    def before_question_index(index: int) -> FeaturePredicate:
        return lambda f: f.computed_at_question_index < index

    @staticmethod
    def is_low_confidence() -> FeaturePredicate:
        return lambda f: f.quality.confidence.is_low

    @staticmethod
    def all_of(*predicates: FeaturePredicate) -> FeaturePredicate:
        """Logical AND of multiple predicates."""
        return lambda f: all(p(f) for p in predicates)

    @staticmethod
    def any_of(*predicates: FeaturePredicate) -> FeaturePredicate:
        """Logical OR of multiple predicates."""
        return lambda f: any(p(f) for p in predicates)

    @staticmethod
    def not_of(predicate: FeaturePredicate) -> FeaturePredicate:
        """Logical NOT of a predicate."""
        return lambda f: not predicate(f)
