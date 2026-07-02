# tests/services/feature_engine/test_feature_engine_diagnostics.py

import pytest
from pydantic import ValidationError

from services.feature_engine.feature_engine_diagnostics import (
    FeatureEngineDiagnostics,
    UpdaterInvocationRecord,
)
from services.feature_engine.feature_engine_metrics import FeatureEngineMetrics
from services.feature_engine.feature_resolution_report import FeatureResolutionReport
from services.feature_engine.feature_update_plan import FeatureUpdatePlan


def _make_plan(**kw) -> FeatureUpdatePlan:
    defaults = dict(session_id="s", candidate_identity_id="c", current_question_index=0)
    defaults.update(kw)
    return FeatureUpdatePlan(**defaults)


def _make_metrics(**kw) -> FeatureEngineMetrics:
    defaults = dict(session_id="s", candidate_identity_id="c", current_question_index=0)
    defaults.update(kw)
    return FeatureEngineMetrics(**defaults)


def _make_report(**kw) -> FeatureResolutionReport:
    defaults = dict(session_id="s", candidate_identity_id="c", current_question_index=0)
    defaults.update(kw)
    return FeatureResolutionReport(**defaults)


def _make_diagnostics(**kw) -> FeatureEngineDiagnostics:
    defaults = dict(
        session_id="sess-001",
        candidate_identity_id="cand-001",
        current_question_index=0,
        plan=_make_plan(),
        resolution_report=_make_report(),
        metrics=_make_metrics(),
    )
    defaults.update(kw)
    return FeatureEngineDiagnostics(**defaults)


class TestUpdaterInvocationRecord:
    def test_valid(self) -> None:
        r = UpdaterInvocationRecord(updater_id="u", invocation_order=1)
        assert r.updater_id == "u"

    def test_defaults(self) -> None:
        r = UpdaterInvocationRecord(updater_id="u", invocation_order=0)
        assert r.observation_ids_received == ()
        assert r.candidate_feature_type_ids_produced == ()
        assert r.duration_ms == 0.0

    def test_negative_order_rejected(self) -> None:
        with pytest.raises(ValidationError):
            UpdaterInvocationRecord(updater_id="u", invocation_order=-1)

    def test_negative_duration_rejected(self) -> None:
        with pytest.raises(ValidationError):
            UpdaterInvocationRecord(updater_id="u", invocation_order=1, duration_ms=-1.0)

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            UpdaterInvocationRecord(updater_id="u", invocation_order=1, unknown="x")

    def test_immutable(self) -> None:
        r = UpdaterInvocationRecord(updater_id="u", invocation_order=1)
        with pytest.raises(ValidationError):
            r.updater_id = "v"  # type: ignore[misc]


class TestFeatureEngineDiagnostics:
    def test_valid_construction(self) -> None:
        diag = _make_diagnostics()
        assert diag.session_id == "sess-001"

    def test_default_is_replay_false(self) -> None:
        assert _make_diagnostics().is_replay is False

    def test_default_delta_summary_none(self) -> None:
        assert _make_diagnostics().reconstruction_delta_summary is None

    def test_with_delta_summary(self) -> None:
        diag = _make_diagnostics(reconstruction_delta_summary="~reasoning:HIGH->LOW")
        assert "reasoning" in (diag.reconstruction_delta_summary or "")

    def test_with_invocation_records(self) -> None:
        record = UpdaterInvocationRecord(updater_id="u", invocation_order=1)
        diag = _make_diagnostics(updater_invocation_records=(record,))
        assert len(diag.updater_invocation_records) == 1

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            _make_diagnostics(unknown="x")

    def test_immutable(self) -> None:
        diag = _make_diagnostics()
        with pytest.raises(ValidationError):
            diag.is_replay = True  # type: ignore[misc]

    def test_default_schema_version(self) -> None:
        assert _make_diagnostics().schema_version == "1.0"

    def test_negative_question_index_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_diagnostics(current_question_index=-1)

    def test_empty_session_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_diagnostics(session_id="")


class TestFeatureEngineDiagnosticsIntegration:
    """Run engine and validate diagnostics structure."""

    def test_diagnostics_from_full_run(self) -> None:
        from domain.contracts.feature.feature_type import FeatureType
        from services.feature_engine.feature_engine import FeatureEngine
        from tests.services.feature_engine.conftest import (
            PassthroughComposer, StubUpdater, make_candidate, make_context,
        )
        updater = StubUpdater(candidates_to_produce=[make_candidate(FeatureType.REASONING)])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        diag = result.diagnostics
        assert diag.plan is not None
        assert diag.resolution_report is not None
        assert diag.metrics is not None

    def test_updater_invocation_record_ids_match_registered(self) -> None:
        from domain.contracts.feature.feature_type import FeatureType
        from services.feature_engine.feature_engine import FeatureEngine
        from tests.services.feature_engine.conftest import (
            PassthroughComposer, StubUpdater, make_candidate, make_context,
        )
        updater = StubUpdater(
            updater_id="my_updater",
            candidates_to_produce=[make_candidate(FeatureType.TREND)],
        )
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        ids = [r.updater_id for r in result.diagnostics.updater_invocation_records]
        assert "my_updater" in ids
