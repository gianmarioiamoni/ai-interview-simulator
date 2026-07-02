# tests/domain/observation/runtime/test_observation_statistics.py

from __future__ import annotations

import pytest

from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType
from domain.observation.runtime.observation_statistics import ObservationStatistics
from tests.domain.observation.runtime.conftest import make_obs


class TestObservationStatisticsEmpty:
    def test_empty_statistics(self):
        stats = ObservationStatistics.from_observations([])
        assert stats.total == 0
        assert stats.is_empty
        assert stats.mean_confidence is None
        assert stats.mean_weight is None
        assert stats.active_share == 0.0


class TestObservationStatisticsComputed:
    def test_total_count(self):
        obs = [make_obs(i) for i in range(5)]
        stats = ObservationStatistics.from_observations(obs)
        assert stats.total == 5

    def test_active_count(self):
        obs = [
            make_obs(0),
            make_obs(1, status=ObservationStatus.DECAYED),
            make_obs(2, status=ObservationStatus.EXPIRED),
            make_obs(3, status=ObservationStatus.SUPERSEDED),
        ]
        stats = ObservationStatistics.from_observations(obs)
        assert stats.active_count == 1
        assert stats.decayed_count == 1
        assert stats.expired_count == 1
        assert stats.superseded_count == 1

    def test_mean_confidence(self):
        obs = [make_obs(0, confidence=0.4), make_obs(1, confidence=0.8)]
        stats = ObservationStatistics.from_observations(obs)
        assert stats.mean_confidence == pytest.approx(0.6)

    def test_min_max_confidence(self):
        obs = [make_obs(0, confidence=0.2), make_obs(1, confidence=0.9)]
        stats = ObservationStatistics.from_observations(obs)
        assert stats.min_confidence == pytest.approx(0.2)
        assert stats.max_confidence == pytest.approx(0.9)

    def test_distinct_types(self):
        obs = [
            make_obs(0, ObservationType.KNOWLEDGE_GAP),
            make_obs(1, ObservationType.TECHNICAL_CORRECTNESS),
            make_obs(2, ObservationType.KNOWLEDGE_GAP),
        ]
        stats = ObservationStatistics.from_observations(obs)
        assert stats.distinct_types == 2

    def test_distinct_question_indices(self):
        obs = [make_obs(0), make_obs(1), make_obs(1)]
        stats = ObservationStatistics.from_observations(obs)
        assert stats.distinct_question_indices == 2

    def test_type_distribution_sorted_by_count_desc(self):
        obs = [
            make_obs(0, ObservationType.KNOWLEDGE_GAP),
            make_obs(1, ObservationType.KNOWLEDGE_GAP),
            make_obs(2, ObservationType.TECHNICAL_CORRECTNESS),
        ]
        stats = ObservationStatistics.from_observations(obs)
        assert stats.type_distribution[0].observation_type == ObservationType.KNOWLEDGE_GAP
        assert stats.type_distribution[0].count == 2

    def test_active_share(self):
        obs = [make_obs(0), make_obs(1, status=ObservationStatus.DECAYED)]
        stats = ObservationStatistics.from_observations(obs)
        assert stats.active_share == pytest.approx(0.5)

    def test_immutable(self):
        stats = ObservationStatistics.from_observations([make_obs(0)])
        with pytest.raises(Exception):
            stats.total = 99  # type: ignore[misc]
