# tests/domain/observation/runtime/test_observation_delta.py

from __future__ import annotations

import pytest

from domain.contracts.observation.observation_status import ObservationStatus
from domain.observation.runtime.observation_delta import ObservationDelta
from tests.domain.observation.runtime.conftest import make_obs


class TestObservationDeltaEmpty:
    def test_identical_populations_no_delta(self):
        obs = [make_obs(i) for i in range(3)]
        delta = ObservationDelta.compute(obs, obs)
        assert delta.is_empty
        assert delta.total_changes == 0

    def test_empty_baseline_all_added(self):
        obs = [make_obs(i) for i in range(3)]
        delta = ObservationDelta.compute([], obs)
        assert len(delta.added) == 3
        assert delta.removed == ()
        assert delta.superseded == ()


class TestObservationDeltaAdded:
    def test_new_observations_appear_in_added(self):
        baseline = [make_obs(0)]
        new_obs = make_obs(1)
        revised = [make_obs(0), new_obs]
        delta = ObservationDelta.compute(baseline, revised)
        added_ids = {o.id.value for o in delta.added}
        assert new_obs.id.value in added_ids


class TestObservationDeltaRemoved:
    def test_removed_observations_detected(self):
        obs0 = make_obs(0)
        obs1 = make_obs(1)
        delta = ObservationDelta.compute([obs0, obs1], [obs0])
        assert len(delta.removed) == 1
        assert delta.removed[0].id == obs1.id


class TestObservationDeltaSuperseded:
    def test_active_to_superseded_classified(self):
        obs_base = make_obs(0)
        obs_revised = obs_base.with_status(ObservationStatus.SUPERSEDED)
        delta = ObservationDelta.compute([obs_base], [obs_revised])
        assert len(delta.superseded) == 1
        assert delta.superseded[0].status == ObservationStatus.SUPERSEDED


class TestObservationDeltaExpired:
    def test_active_to_expired_classified(self):
        obs_base = make_obs(0)
        obs_revised = obs_base.with_status(ObservationStatus.EXPIRED)
        delta = ObservationDelta.compute([obs_base], [obs_revised])
        assert len(delta.expired) == 1

    def test_already_expired_to_expired_not_reclassified(self):
        obs = make_obs(0, status=ObservationStatus.EXPIRED)
        delta = ObservationDelta.compute([obs], [obs])
        assert delta.is_empty


class TestObservationDeltaImmutability:
    def test_delta_is_immutable(self):
        delta = ObservationDelta.compute([], [])
        with pytest.raises(Exception):
            delta.added = ()  # type: ignore[misc]
