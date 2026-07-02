# tests/domain/contracts/observation/test_observation_origin.py

import pytest

from domain.contracts.observation.observation_origin import ObservationOrigin


class TestObservationOriginValues:
    def test_evaluation_value(self):
        assert ObservationOrigin.EVALUATION == "evaluation"

    def test_evidence_signal_value(self):
        assert ObservationOrigin.EVIDENCE_SIGNAL == "evidence_signal"

    def test_pattern_detector_value(self):
        assert ObservationOrigin.PATTERN_DETECTOR == "pattern_detector"

    def test_replay_value(self):
        assert ObservationOrigin.REPLAY == "replay"

    def test_calibration_value(self):
        assert ObservationOrigin.CALIBRATION == "calibration"

    def test_is_str_enum(self):
        assert isinstance(ObservationOrigin.EVALUATION, str)

    def test_exactly_five_origins(self):
        assert len(ObservationOrigin) == 5

    def test_all_values_unique(self):
        values = [o.value for o in ObservationOrigin]
        assert len(values) == len(set(values))

    def test_all_values_lowercase(self):
        for o in ObservationOrigin:
            assert o.value == o.value.lower()


class TestObservationOriginLookup:
    def test_lookup_evaluation(self):
        assert ObservationOrigin("evaluation") is ObservationOrigin.EVALUATION

    def test_lookup_evidence_signal(self):
        assert ObservationOrigin("evidence_signal") is ObservationOrigin.EVIDENCE_SIGNAL

    def test_lookup_pattern_detector(self):
        assert ObservationOrigin("pattern_detector") is ObservationOrigin.PATTERN_DETECTOR

    def test_lookup_replay(self):
        assert ObservationOrigin("replay") is ObservationOrigin.REPLAY

    def test_lookup_calibration(self):
        assert ObservationOrigin("calibration") is ObservationOrigin.CALIBRATION

    def test_invalid_origin_raises(self):
        with pytest.raises(ValueError):
            ObservationOrigin("unknown_origin")

    def test_runtime_origins_are_three(self):
        runtime = {ObservationOrigin.EVALUATION, ObservationOrigin.EVIDENCE_SIGNAL, ObservationOrigin.PATTERN_DETECTOR}
        assert len(runtime) == 3

    def test_non_runtime_origins_are_two(self):
        non_runtime = {ObservationOrigin.REPLAY, ObservationOrigin.CALIBRATION}
        assert len(non_runtime) == 2
