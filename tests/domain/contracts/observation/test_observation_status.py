# tests/domain/contracts/observation/test_observation_status.py

import pytest

from domain.contracts.observation.observation_status import ObservationStatus


class TestObservationStatusValues:
    def test_active_value(self):
        assert ObservationStatus.ACTIVE == "active"

    def test_decayed_value(self):
        assert ObservationStatus.DECAYED == "decayed"

    def test_expired_value(self):
        assert ObservationStatus.EXPIRED == "expired"

    def test_superseded_value(self):
        assert ObservationStatus.SUPERSEDED == "superseded"

    def test_is_str_enum(self):
        assert isinstance(ObservationStatus.ACTIVE, str)

    def test_exactly_four_statuses(self):
        assert len(ObservationStatus) == 4

    def test_all_values_unique(self):
        values = [s.value for s in ObservationStatus]
        assert len(values) == len(set(values))

    def test_all_values_lowercase(self):
        for s in ObservationStatus:
            assert s.value == s.value.lower()


class TestObservationStatusLookup:
    def test_lookup_active(self):
        assert ObservationStatus("active") is ObservationStatus.ACTIVE

    def test_lookup_decayed(self):
        assert ObservationStatus("decayed") is ObservationStatus.DECAYED

    def test_lookup_expired(self):
        assert ObservationStatus("expired") is ObservationStatus.EXPIRED

    def test_lookup_superseded(self):
        assert ObservationStatus("superseded") is ObservationStatus.SUPERSEDED

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError):
            ObservationStatus("pending")
