# tests/services/feature_engine/test_feature_engine_metrics.py

import pytest
from pydantic import ValidationError

from services.feature_engine.feature_engine_metrics import (
    FeatureEngineMetrics,
    UpdaterTimingRecord,
)


def _make_timing(**kwargs) -> UpdaterTimingRecord:
    defaults = dict(updater_id="stub_updater", duration_ms=5.0, candidates_produced=1)
    defaults.update(kwargs)
    return UpdaterTimingRecord(**defaults)


def _make_metrics(**kwargs) -> FeatureEngineMetrics:
    defaults = dict(
        session_id="sess-001",
        candidate_identity_id="cand-001",
        current_question_index=0,
    )
    defaults.update(kwargs)
    return FeatureEngineMetrics(**defaults)


class TestUpdaterTimingRecord:
    def test_valid(self) -> None:
        t = _make_timing()
        assert t.updater_id == "stub_updater"
        assert t.duration_ms == 5.0

    def test_zero_duration(self) -> None:
        t = _make_timing(duration_ms=0.0)
        assert t.duration_ms == 0.0

    def test_negative_duration_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_timing(duration_ms=-1.0)

    def test_negative_candidates_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_timing(candidates_produced=-1)

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            _make_timing(unknown="x")

    def test_immutable(self) -> None:
        t = _make_timing()
        with pytest.raises(ValidationError):
            t.duration_ms = 99.0  # type: ignore[misc]


class TestFeatureEngineMetrics:
    def test_minimal_valid(self) -> None:
        m = _make_metrics()
        assert m.session_id == "sess-001"

    def test_default_durations_zero(self) -> None:
        m = _make_metrics()
        assert m.total_cycle_duration_ms == 0.0
        assert m.composer_duration_ms == 0.0
        assert m.commit_duration_ms == 0.0

    def test_default_counts_zero(self) -> None:
        m = _make_metrics()
        assert m.features_computed == 0
        assert m.candidates_collected == 0
        assert m.observation_count == 0

    def test_default_flags_false(self) -> None:
        m = _make_metrics()
        assert m.is_incremental is False
        assert m.is_replay is False

    def test_with_updater_timings(self) -> None:
        t = _make_timing()
        m = _make_metrics(updater_timings=(t,))
        assert len(m.updater_timings) == 1

    def test_incremental_flag(self) -> None:
        m = _make_metrics(is_incremental=True)
        assert m.is_incremental is True

    def test_replay_flag(self) -> None:
        m = _make_metrics(is_replay=True)
        assert m.is_replay is True

    def test_negative_duration_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_metrics(total_cycle_duration_ms=-1.0)

    def test_negative_features_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_metrics(features_computed=-1)

    def test_empty_session_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_metrics(session_id="")

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            _make_metrics(unknown="x")

    def test_immutable(self) -> None:
        m = _make_metrics()
        with pytest.raises(ValidationError):
            m.features_computed = 5  # type: ignore[misc]

    def test_default_schema_version(self) -> None:
        assert _make_metrics().schema_version == "1.0"
