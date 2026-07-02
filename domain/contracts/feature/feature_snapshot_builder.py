# domain/contracts/feature/feature_snapshot_builder.py
# FeatureSnapshotBuilder — assembles FeatureCollection from FeatureEngineResult (E01-M4)

from __future__ import annotations

from domain.contracts.feature.feature_collection import FeatureCollection
from domain.contracts.feature.feature_statistics import FeatureStatistics
from domain.contracts.feature.profile_feature import ProfileFeature


class FeatureSnapshot:
    """Assembled read-only view of a FeatureEngine cycle output.

    Combines FeatureCollection + FeatureStatistics.
    Immutable after construction.

    This is NOT a Pydantic model intentionally — it is a lightweight runtime
    value object that holds pre-computed views without serialisation overhead.
    """

    __slots__ = ("_collection", "_statistics", "_question_index", "_session_id")

    def __init__(
        self,
        collection: FeatureCollection,
        statistics: FeatureStatistics,
        question_index: int,
        session_id: str,
    ) -> None:
        self._collection = collection
        self._statistics = statistics
        self._question_index = question_index
        self._session_id = session_id

    @property
    def collection(self) -> FeatureCollection:
        return self._collection

    @property
    def statistics(self) -> FeatureStatistics:
        return self._statistics

    @property
    def question_index(self) -> int:
        return self._question_index

    @property
    def session_id(self) -> str:
        return self._session_id

    def __repr__(self) -> str:
        return (
            f"FeatureSnapshot(session={self._session_id!r}, "
            f"q={self._question_index}, "
            f"features={self._collection.size})"
        )


class FeatureSnapshotBuilder:
    """Assembles a FeatureSnapshot from a sequence of ProfileFeatures.

    Accepts the raw features tuple emitted by FeatureEngineResult so that
    callers never need to know the internal layout of FeatureCollection or
    FeatureStatistics.

    Usage:
        snapshot = FeatureSnapshotBuilder.build(
            features=result.features,
            session_id=result.session_id,
            question_index=result.current_question_index,
        )
    """

    @staticmethod
    def build(
        features: tuple[ProfileFeature, ...] | list[ProfileFeature],
        session_id: str,
        question_index: int,
    ) -> FeatureSnapshot:
        collection = FeatureCollection.from_iterable(list(features))
        statistics = FeatureStatistics.from_collection(collection)
        return FeatureSnapshot(
            collection=collection,
            statistics=statistics,
            question_index=question_index,
            session_id=session_id,
        )

    @staticmethod
    def empty(session_id: str, question_index: int) -> FeatureSnapshot:
        """Return an empty snapshot (e.g. after a failed FeatureEngine cycle)."""
        return FeatureSnapshotBuilder.build(
            features=(),
            session_id=session_id,
            question_index=question_index,
        )
