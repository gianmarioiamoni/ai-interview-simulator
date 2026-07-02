# domain/contracts/coaching/coaching_collection.py
# CoachingCollection — runtime container for objectives, actions, and recommendations

from __future__ import annotations

from collections import defaultdict
from typing import Callable

from domain.contracts.coaching.coaching_action import CoachingAction, ActionCategory
from domain.contracts.coaching.learning_objective import LearningObjective, ObjectivePriority
from domain.contracts.coaching.study_recommendation import StudyRecommendation
from domain.contracts.feature.feature_type import FeatureType


class CoachingCollection:
    """Immutable, queryable container of coaching runtime objects.

    Holds LearningObjectives, CoachingActions, and StudyRecommendations.
    All query operations return new collections or plain structures without
    mutating internal state (ADR-025).

    Not a Pydantic model — lightweight runtime value object.
    """

    __slots__ = ("_objectives", "_actions", "_recommendations")

    def __init__(
        self,
        objectives: tuple[LearningObjective, ...],
        actions: tuple[CoachingAction, ...],
        recommendations: tuple[StudyRecommendation, ...],
    ) -> None:
        self._objectives = objectives
        self._actions = actions
        self._recommendations = recommendations

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def empty(cls) -> "CoachingCollection":
        return cls(objectives=(), actions=(), recommendations=())

    @classmethod
    def from_parts(
        cls,
        objectives: list[LearningObjective] | tuple[LearningObjective, ...],
        actions: list[CoachingAction] | tuple[CoachingAction, ...],
        recommendations: list[StudyRecommendation] | tuple[StudyRecommendation, ...],
    ) -> "CoachingCollection":
        return cls(
            objectives=tuple(objectives),
            actions=tuple(actions),
            recommendations=tuple(recommendations),
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def objectives(self) -> tuple[LearningObjective, ...]:
        return self._objectives

    @property
    def actions(self) -> tuple[CoachingAction, ...]:
        return self._actions

    @property
    def recommendations(self) -> tuple[StudyRecommendation, ...]:
        return self._recommendations

    @property
    def objective_count(self) -> int:
        return len(self._objectives)

    @property
    def action_count(self) -> int:
        return len(self._actions)

    @property
    def recommendation_count(self) -> int:
        return len(self._recommendations)

    @property
    def is_empty(self) -> bool:
        return not self._objectives and not self._actions and not self._recommendations

    # ------------------------------------------------------------------
    # Objective queries
    # ------------------------------------------------------------------

    def objectives_by_priority(self, priority: ObjectivePriority) -> tuple[LearningObjective, ...]:
        return tuple(o for o in self._objectives if o.priority == priority)

    def objectives_by_feature_type(self, feature_type: FeatureType) -> tuple[LearningObjective, ...]:
        return tuple(o for o in self._objectives if o.feature_type == feature_type)

    def objective_by_id(self, objective_id: str) -> LearningObjective | None:
        for o in self._objectives:
            if o.objective_id == objective_id:
                return o
        return None

    def filter_objectives(
        self, predicate: Callable[[LearningObjective], bool]
    ) -> "CoachingCollection":
        filtered = tuple(o for o in self._objectives if predicate(o))
        return CoachingCollection(
            objectives=filtered,
            actions=self._actions,
            recommendations=self._recommendations,
        )

    # ------------------------------------------------------------------
    # Action queries
    # ------------------------------------------------------------------

    def actions_for_objective(self, objective_id: str) -> tuple[CoachingAction, ...]:
        return tuple(a for a in self._actions if a.objective_id == objective_id)

    def actions_by_category(self, category: ActionCategory) -> tuple[CoachingAction, ...]:
        return tuple(a for a in self._actions if a.category == category)

    def immediate_actions(self) -> tuple[CoachingAction, ...]:
        return tuple(a for a in self._actions if a.is_immediate)

    # ------------------------------------------------------------------
    # Recommendation queries
    # ------------------------------------------------------------------

    def recommendations_for_objective(self, objective_id: str) -> tuple[StudyRecommendation, ...]:
        return tuple(r for r in self._recommendations if r.objective_id == objective_id)

    # ------------------------------------------------------------------
    # Grouping
    # ------------------------------------------------------------------

    def group_objectives_by_feature_type(self) -> dict[FeatureType, tuple[LearningObjective, ...]]:
        groups: dict[FeatureType, list[LearningObjective]] = defaultdict(list)
        for o in self._objectives:
            groups[o.feature_type].append(o)
        return {k: tuple(v) for k, v in groups.items()}

    def group_objectives_by_priority(self) -> dict[ObjectivePriority, tuple[LearningObjective, ...]]:
        groups: dict[ObjectivePriority, list[LearningObjective]] = defaultdict(list)
        for o in self._objectives:
            groups[o.priority].append(o)
        return {k: tuple(v) for k, v in groups.items()}
