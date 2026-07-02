# tests/domain/observation/runtime/test_observation_collection.py

from __future__ import annotations

import pytest

from domain.contracts.observation.observation_filter import ObservationFilter
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType
from domain.observation.runtime.observation_collection import ObservationCollection
from domain.observation.runtime.observation_ordering import ObservationOrderingPolicy
from tests.domain.observation.runtime.conftest import make_obs, SESSION


class TestObservationCollectionFiltering:
    def test_filter_by_type(self):
        obs = [
            make_obs(0, ObservationType.TECHNICAL_CORRECTNESS),
            make_obs(1, ObservationType.KNOWLEDGE_GAP),
        ]
        col = ObservationCollection.from_list(obs)
        filtered = col.filter(ObservationFilter(observation_types=frozenset({ObservationType.KNOWLEDGE_GAP})))
        assert filtered.size == 1

    def test_active_only(self):
        obs = [
            make_obs(0),
            make_obs(1, status=ObservationStatus.DECAYED),
            make_obs(2, status=ObservationStatus.SUPERSEDED),
        ]
        col = ObservationCollection.from_list(obs)
        assert col.active().size == 1

    def test_by_type(self):
        obs = [make_obs(0, ObservationType.KNOWLEDGE_GAP), make_obs(1, ObservationType.TECHNICAL_CORRECTNESS)]
        col = ObservationCollection.from_list(obs)
        assert col.by_type(ObservationType.KNOWLEDGE_GAP).size == 1

    def test_by_origin(self):
        obs = [
            make_obs(0, origin=ObservationOrigin.EVALUATION),
            make_obs(1, origin=ObservationOrigin.REPLAY),
        ]
        col = ObservationCollection.from_list(obs)
        assert col.by_origin(ObservationOrigin.REPLAY).size == 1

    def test_by_question_index(self):
        obs = [make_obs(0), make_obs(1), make_obs(2)]
        col = ObservationCollection.from_list(obs)
        assert col.by_question_index(1).size == 1

    def test_with_min_confidence(self):
        obs = [make_obs(0, confidence=0.3), make_obs(1, confidence=0.9)]
        col = ObservationCollection.from_list(obs)
        assert col.with_min_confidence(0.8).size == 1

    def test_tags_all_filter(self):
        obs1 = make_obs(0, tags=frozenset({"a", "b"}))
        obs2 = make_obs(1, tags=frozenset({"a"}))
        col = ObservationCollection.from_list([obs1, obs2])
        filtered = col.filter(ObservationFilter(tags_all=frozenset({"a", "b"})))
        assert filtered.size == 1

    def test_tags_any_filter(self):
        obs1 = make_obs(0, tags=frozenset({"x"}))
        obs2 = make_obs(1, tags=frozenset({"y"}))
        col = ObservationCollection.from_list([obs1, obs2])
        filtered = col.filter(ObservationFilter(tags_any=frozenset({"x"})))
        assert filtered.size == 1


class TestObservationCollectionGrouping:
    def test_group_by_type(self):
        obs = [
            make_obs(0, ObservationType.KNOWLEDGE_GAP),
            make_obs(1, ObservationType.KNOWLEDGE_GAP),
            make_obs(2, ObservationType.TECHNICAL_CORRECTNESS),
        ]
        col = ObservationCollection.from_list(obs)
        groups = col.group_by_type()
        assert len(groups[ObservationType.KNOWLEDGE_GAP]) == 2
        assert len(groups[ObservationType.TECHNICAL_CORRECTNESS]) == 1

    def test_group_by_question_index_sorted(self):
        obs = [make_obs(2), make_obs(0), make_obs(1)]
        col = ObservationCollection.from_list(obs)
        groups = col.group_by_question_index()
        assert list(groups.keys()) == [0, 1, 2]

    def test_group_by_status(self):
        obs = [make_obs(0), make_obs(1, status=ObservationStatus.DECAYED)]
        col = ObservationCollection.from_list(obs)
        groups = col.group_by_status()
        assert len(groups[ObservationStatus.ACTIVE]) == 1
        assert len(groups[ObservationStatus.DECAYED]) == 1


class TestObservationCollectionAggregation:
    def test_average_confidence(self):
        obs = [make_obs(0, confidence=0.4), make_obs(1, confidence=0.8)]
        col = ObservationCollection.from_list(obs)
        assert col.average_confidence() == pytest.approx(0.6)

    def test_average_confidence_empty_returns_none(self):
        assert ObservationCollection.from_list([]).average_confidence() is None

    def test_count_by_type(self):
        obs = [make_obs(0, ObservationType.KNOWLEDGE_GAP), make_obs(1, ObservationType.KNOWLEDGE_GAP)]
        col = ObservationCollection.from_list(obs)
        counts = col.count_by_type()
        assert counts[ObservationType.KNOWLEDGE_GAP] == 2

    def test_distinct_types(self):
        obs = [
            make_obs(0, ObservationType.TECHNICAL_CORRECTNESS),
            make_obs(1, ObservationType.KNOWLEDGE_GAP),
            make_obs(2, ObservationType.TECHNICAL_CORRECTNESS),
        ]
        col = ObservationCollection.from_list(obs)
        assert len(col.distinct_types()) == 2

    def test_top_by_confidence(self):
        obs = [make_obs(i, confidence=0.1 * (i + 1)) for i in range(5)]
        col = ObservationCollection.from_list(obs)
        top2 = col.top_by_confidence(2)
        assert len(top2) == 2
        assert top2[0].confidence > top2[1].confidence

    def test_ordered_returns_new_collection(self):
        obs = [make_obs(2), make_obs(0), make_obs(1)]
        col = ObservationCollection.from_list(obs)
        ordered = col.ordered(ObservationOrderingPolicy.CHRONOLOGICAL)
        indices = [o.metadata.question_index for o in ordered.all]
        assert indices == [0, 1, 2]
