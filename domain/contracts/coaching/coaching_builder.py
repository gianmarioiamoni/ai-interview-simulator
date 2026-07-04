# domain/contracts/coaching/coaching_builder.py
# CoachingBuilder — assembles CoachingCollection + CoachingStatistics (ADR-025)

from __future__ import annotations

from domain.contracts.coaching.coaching_action import CoachingAction
from domain.contracts.coaching.coaching_collection import CoachingCollection
from domain.contracts.coaching.coaching_statistics import CoachingStatistics
from domain.contracts.coaching.learning_objective import LearningObjective
from domain.contracts.coaching.study_recommendation import StudyRecommendation


class CoachingSnapshot:
    """Assembled read-only view of a coaching computation cycle.

    Combines CoachingCollection + CoachingStatistics.
    Immutable after construction. Not a Pydantic model — lightweight runtime
    value object.
    """

    __slots__ = ("_collection", "_statistics", "_question_index", "_session_id")

    def __init__(
        self,
        collection: CoachingCollection,
        statistics: CoachingStatistics,
        question_index: int,
        session_id: str,
    ) -> None:
        self._collection = collection
        self._statistics = statistics
        self._question_index = question_index
        self._session_id = session_id

    @property
    def collection(self) -> CoachingCollection:
        return self._collection

    @property
    def statistics(self) -> CoachingStatistics:
        return self._statistics

    @property
    def question_index(self) -> int:
        return self._question_index

    @property
    def session_id(self) -> str:
        return self._session_id

    def __repr__(self) -> str:
        return (
            f"CoachingSnapshot(session={self._session_id!r}, "
            f"q={self._question_index}, "
            f"objectives={self._statistics.total_objectives})"
        )


class CoachingBuilder:
    """Assembles a CoachingSnapshot from coaching runtime objects.

    Pure factory — no state, no narrative generation, no CandidateProfile mutation.
    """

    @staticmethod
    def build(
        objectives: tuple[LearningObjective, ...] | list[LearningObjective],
        actions: tuple[CoachingAction, ...] | list[CoachingAction],
        recommendations: tuple[StudyRecommendation, ...] | list[StudyRecommendation],
        session_id: str,
        question_index: int,
    ) -> CoachingSnapshot:
        collection = CoachingCollection.from_parts(
            objectives=objectives,
            actions=actions,
            recommendations=recommendations,
        )
        statistics = CoachingStatistics.from_collection(collection)
        return CoachingSnapshot(
            collection=collection,
            statistics=statistics,
            question_index=question_index,
            session_id=session_id,
        )

    @staticmethod
    def empty(session_id: str, question_index: int) -> CoachingSnapshot:
        """Return an empty snapshot for sessions with no coaching output."""
        return CoachingBuilder.build(
            objectives=(),
            actions=(),
            recommendations=(),
            session_id=session_id,
            question_index=question_index,
        )
