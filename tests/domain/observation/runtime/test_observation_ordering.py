# tests/domain/observation/runtime/test_observation_ordering.py

from __future__ import annotations

import pytest

from domain.contracts.observation.observation_query import ObservationSortField, ObservationSortOrder
from domain.contracts.observation.observation_type import ObservationType
from domain.observation.runtime.observation_ordering import ObservationOrdering, ObservationOrderingPolicy
from tests.domain.observation.runtime.conftest import make_obs


class TestObservationOrderingPolicies:
    def test_chronological_asc(self):
        obs = [make_obs(3), make_obs(1), make_obs(2)]
        result = ObservationOrdering.apply(tuple(obs), ObservationOrderingPolicy.CHRONOLOGICAL)
        indices = [o.metadata.question_index for o in result]
        assert indices == [1, 2, 3]

    def test_reverse_chronological_desc(self):
        obs = [make_obs(1), make_obs(2), make_obs(3)]
        result = ObservationOrdering.apply(tuple(obs), ObservationOrderingPolicy.REVERSE_CHRONOLOGICAL)
        indices = [o.metadata.question_index for o in result]
        assert indices == [3, 2, 1]

    def test_confidence_desc(self):
        obs = [make_obs(0, confidence=0.3), make_obs(1, confidence=0.9), make_obs(2, confidence=0.6)]
        result = ObservationOrdering.apply(tuple(obs), ObservationOrderingPolicy.CONFIDENCE_DESC)
        assert result[0].confidence == pytest.approx(0.9)
        assert result[-1].confidence == pytest.approx(0.3)

    def test_confidence_asc(self):
        obs = [make_obs(0, confidence=0.9), make_obs(1, confidence=0.1)]
        result = ObservationOrdering.apply(tuple(obs), ObservationOrderingPolicy.CONFIDENCE_ASC)
        assert result[0].confidence == pytest.approx(0.1)

    def test_weight_desc(self):
        obs = [make_obs(0, weight=0.2), make_obs(1, weight=0.8), make_obs(2, weight=0.5)]
        result = ObservationOrdering.apply(tuple(obs), ObservationOrderingPolicy.WEIGHT_DESC)
        assert result[0].weight == pytest.approx(0.8)

    def test_type_then_chronological(self):
        obs = [
            make_obs(2, ObservationType.KNOWLEDGE_GAP),
            make_obs(0, ObservationType.TECHNICAL_CORRECTNESS),
            make_obs(1, ObservationType.KNOWLEDGE_GAP),
        ]
        result = ObservationOrdering.apply(tuple(obs), ObservationOrderingPolicy.TYPE_THEN_CHRONOLOGICAL)
        # knowledge_gap < technical_correctness alphabetically; knowledge_gap entries ordered q=1,q=2
        assert result[0].observation_type == ObservationType.KNOWLEDGE_GAP
        assert result[0].metadata.question_index == 1
        assert result[1].observation_type == ObservationType.KNOWLEDGE_GAP
        assert result[1].metadata.question_index == 2
        assert result[2].observation_type == ObservationType.TECHNICAL_CORRECTNESS

    def test_returns_new_tuple_does_not_mutate(self):
        obs_tuple = tuple(make_obs(i) for i in range(3, 0, -1))
        result = ObservationOrdering.apply(obs_tuple, ObservationOrderingPolicy.CHRONOLOGICAL)
        assert obs_tuple[0].metadata.question_index == 3
        assert result[0].metadata.question_index == 1


class TestObservationOrderingFromQueryFields:
    def test_from_query_sort_desc(self):
        obs = [make_obs(0, confidence=0.1), make_obs(1, confidence=0.9)]
        result = ObservationOrdering.from_query_fields(
            obs, ObservationSortField.CONFIDENCE, ObservationSortOrder.DESC
        )
        assert result[0].confidence == pytest.approx(0.9)

    def test_is_chronological_check(self):
        ordered = tuple(make_obs(i) for i in range(5))
        unordered = tuple(make_obs(i) for i in [2, 0, 4])
        assert ObservationOrdering.is_chronological(ordered)
        assert not ObservationOrdering.is_chronological(unordered)
