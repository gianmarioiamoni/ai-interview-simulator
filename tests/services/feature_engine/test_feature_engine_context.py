# tests/services/feature_engine/test_feature_engine_context.py

import pytest
from pydantic import ValidationError

from services.feature_engine.feature_engine_context import FeatureEngineContext
from tests.services.feature_engine.conftest import make_snapshot


def _make_ctx(**kwargs) -> FeatureEngineContext:
    defaults = dict(
        session_id="sess-001",
        candidate_identity_id="cand-001",
        current_question_index=0,
        snapshot=make_snapshot(),
    )
    defaults.update(kwargs)
    return FeatureEngineContext(**defaults)


class TestFeatureEngineContextConstruction:
    def test_minimal_valid(self) -> None:
        ctx = _make_ctx()
        assert ctx.session_id == "sess-001"
        assert ctx.candidate_identity_id == "cand-001"
        assert ctx.current_question_index == 0

    def test_default_engine_version(self) -> None:
        assert _make_ctx().feature_engine_version == "1.0.0"

    def test_default_is_replay_false(self) -> None:
        assert _make_ctx().is_replay is False

    def test_default_schema_version(self) -> None:
        assert _make_ctx().schema_version == "1.0"

    def test_is_replay_true(self) -> None:
        ctx = _make_ctx(is_replay=True)
        assert ctx.is_replay is True

    def test_empty_session_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_ctx(session_id="")

    def test_empty_candidate_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_ctx(candidate_identity_id="")

    def test_negative_question_index_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_ctx(current_question_index=-1)

    def test_empty_engine_version_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_ctx(feature_engine_version="")

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            _make_ctx(unknown_field="x")

    def test_immutable(self) -> None:
        ctx = _make_ctx()
        with pytest.raises(ValidationError):
            ctx.session_id = "other"  # type: ignore[misc]

    def test_equality(self) -> None:
        snap = make_snapshot()
        a = FeatureEngineContext(
            session_id="s", candidate_identity_id="c",
            current_question_index=0, snapshot=snap,
        )
        b = FeatureEngineContext(
            session_id="s", candidate_identity_id="c",
            current_question_index=0, snapshot=snap,
        )
        assert a == b

    def test_custom_engine_version(self) -> None:
        ctx = _make_ctx(feature_engine_version="2.5.1")
        assert ctx.feature_engine_version == "2.5.1"
