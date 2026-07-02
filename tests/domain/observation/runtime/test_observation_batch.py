# tests/domain/observation/runtime/test_observation_batch.py

from __future__ import annotations

import pytest

from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.observation.observation_status import ObservationStatus
from domain.observation.runtime.observation_batch import ObservationBatch
from tests.domain.observation.runtime.conftest import make_obs, SESSION


class TestObservationBatchConstruction:
    def test_from_list_empty(self):
        batch = ObservationBatch.from_list(SESSION, 0, [])
        assert batch.is_empty
        assert batch.size == 0

    def test_from_list_preserves_order(self):
        obs_list = [make_obs(3), make_obs(3), make_obs(3)]
        batch = ObservationBatch.from_list(SESSION, 3, obs_list)
        assert batch.size == 3

    def test_immutable(self):
        batch = ObservationBatch.from_list(SESSION, 0, [])
        with pytest.raises(Exception):
            batch.session_id = "mutated"  # type: ignore[misc]

    def test_session_mismatch_raises(self):
        obs = make_obs(0, session_id="other-session")
        with pytest.raises(ValueError, match="belongs to session"):
            ObservationBatch.from_list(SESSION, 0, [obs])

    def test_question_index_mismatch_raises(self):
        obs = make_obs(5)
        with pytest.raises(ValueError, match="question_index"):
            ObservationBatch.from_list(SESSION, 0, [obs])


class TestObservationBatchQueries:
    def test_by_type_filters(self):
        obs1 = make_obs(0, ObservationType.TECHNICAL_CORRECTNESS)
        obs2 = make_obs(0, ObservationType.KNOWLEDGE_GAP)
        batch = ObservationBatch.from_list(SESSION, 0, [obs1, obs2])
        result = batch.by_type(ObservationType.KNOWLEDGE_GAP)
        assert len(result) == 1
        assert result[0].observation_type == ObservationType.KNOWLEDGE_GAP

    def test_active_filters_active_only(self):
        obs1 = make_obs(0)
        obs2 = make_obs(0, status=ObservationStatus.SUPERSEDED)
        batch = ObservationBatch.from_list(SESSION, 0, [obs1, obs2])
        assert len(batch.active()) == 1

    def test_types_returns_frozenset(self):
        obs1 = make_obs(0, ObservationType.TECHNICAL_CORRECTNESS)
        obs2 = make_obs(0, ObservationType.KNOWLEDGE_GAP)
        batch = ObservationBatch.from_list(SESSION, 0, [obs1, obs2])
        assert batch.types() == frozenset({
            ObservationType.TECHNICAL_CORRECTNESS,
            ObservationType.KNOWLEDGE_GAP,
        })
