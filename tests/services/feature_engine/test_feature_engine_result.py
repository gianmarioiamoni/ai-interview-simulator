# tests/services/feature_engine/test_feature_engine_result.py

import pytest
from pydantic import ValidationError

from domain.contracts.feature.feature_type import FeatureType
from services.feature_engine.feature_engine_result import FeatureEngineResult
from tests.services.feature_engine.conftest import (
    PassthroughComposer,
    StubUpdater,
    make_candidate,
    make_context,
    make_snapshot,
)
from services.feature_engine.feature_engine import FeatureEngine


def _make_engine_and_run(
    feature_type: FeatureType = FeatureType.REASONING,
    value: str = "HIGH",
) -> FeatureEngineResult:
    candidate = make_candidate(feature_type, value)
    updater = StubUpdater(candidates_to_produce=[candidate])
    composer = PassthroughComposer()
    engine = FeatureEngine([updater], composer)
    context = make_context()
    return engine.run(context)


class TestFeatureEngineResult:
    def test_successful_result(self) -> None:
        result = _make_engine_and_run()
        assert result.is_successful is True
        assert result.failure_reason is None

    def test_features_present(self) -> None:
        result = _make_engine_and_run()
        assert len(result.features) == 1

    def test_feature_count_property(self) -> None:
        result = _make_engine_and_run()
        assert result.feature_count == 1

    def test_feature_type_ids_property(self) -> None:
        result = _make_engine_and_run(FeatureType.TREND)
        assert "trend_feature" in result.feature_type_ids

    def test_diagnostics_present(self) -> None:
        result = _make_engine_and_run()
        assert result.diagnostics is not None

    def test_session_id_propagated(self) -> None:
        result = _make_engine_and_run()
        assert result.session_id == "sess-001"

    def test_candidate_id_propagated(self) -> None:
        result = _make_engine_and_run()
        assert result.candidate_identity_id == "cand-001"

    def test_question_index_propagated(self) -> None:
        result = _make_engine_and_run()
        assert result.current_question_index == 0

    def test_default_schema_version(self) -> None:
        result = _make_engine_and_run()
        assert result.schema_version == "1.0"

    def test_result_is_immutable(self) -> None:
        result = _make_engine_and_run()
        with pytest.raises(ValidationError):
            result.is_successful = False  # type: ignore[misc]

    def test_extra_fields_forbidden(self) -> None:
        result = _make_engine_and_run()
        diag = result.diagnostics
        with pytest.raises(ValidationError):
            FeatureEngineResult(
                session_id="s",
                candidate_identity_id="c",
                current_question_index=0,
                diagnostics=diag,
                unknown="x",
            )

    def test_empty_features_on_empty_updater(self) -> None:
        from tests.services.feature_engine.conftest import EmptyUpdater
        engine = FeatureEngine([EmptyUpdater()], PassthroughComposer())
        result = engine.run(make_context())
        assert result.feature_count == 0

    def test_feature_type_ids_multiple(self) -> None:
        c1 = make_candidate(FeatureType.REASONING, "HIGH")
        c2 = make_candidate(FeatureType.TREND, "IMPROVING")
        updater = StubUpdater(
            candidates_to_produce=[c1, c2],
            feature_identity_set=frozenset({"reasoning_feature", "trend_feature"}),
        )
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert "reasoning_feature" in result.feature_type_ids
        assert "trend_feature" in result.feature_type_ids
