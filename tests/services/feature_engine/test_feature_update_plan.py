# tests/services/feature_engine/test_feature_update_plan.py

import pytest
from pydantic import ValidationError

from services.feature_engine.feature_update_plan import (
    FeatureUpdatePlan,
    UpdaterInvocationSpec,
)


def _make_spec(**kwargs) -> UpdaterInvocationSpec:
    defaults = dict(updater_id="obs_updater", invocation_order=1)
    defaults.update(kwargs)
    return UpdaterInvocationSpec(**defaults)


def _make_plan(**kwargs) -> FeatureUpdatePlan:
    defaults = dict(
        session_id="sess-001",
        candidate_identity_id="cand-001",
        current_question_index=0,
    )
    defaults.update(kwargs)
    return FeatureUpdatePlan(**defaults)


class TestUpdaterInvocationSpec:
    def test_minimal_valid(self) -> None:
        spec = _make_spec()
        assert spec.updater_id == "obs_updater"
        assert spec.invocation_order == 1

    def test_default_incremental_false(self) -> None:
        assert _make_spec().is_incremental is False

    def test_default_target_empty(self) -> None:
        assert _make_spec().target_feature_type_ids == frozenset()

    def test_with_targets(self) -> None:
        spec = _make_spec(target_feature_type_ids=frozenset({"reasoning_feature"}))
        assert "reasoning_feature" in spec.target_feature_type_ids

    def test_empty_updater_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_spec(updater_id="")

    def test_negative_order_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_spec(invocation_order=-1)

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            _make_spec(unknown="x")

    def test_immutable(self) -> None:
        spec = _make_spec()
        with pytest.raises(ValidationError):
            spec.updater_id = "other"  # type: ignore[misc]


class TestFeatureUpdatePlan:
    def test_minimal_valid(self) -> None:
        plan = _make_plan()
        assert plan.session_id == "sess-001"

    def test_default_full_recomputation_true(self) -> None:
        assert _make_plan().is_full_recomputation is True

    def test_default_incremental_false(self) -> None:
        assert _make_plan().is_incremental is False

    def test_default_replay_false(self) -> None:
        assert _make_plan().is_replay is False

    def test_with_updater_specs(self) -> None:
        specs = (
            _make_spec(updater_id="obs", invocation_order=1),
            _make_spec(updater_id="cal", invocation_order=2),
        )
        plan = _make_plan(updater_specs=specs)
        assert len(plan.updater_specs) == 2

    def test_incremental_plan(self) -> None:
        plan = _make_plan(
            is_full_recomputation=False,
            is_incremental=True,
            affected_feature_type_ids=frozenset({"reasoning_feature"}),
        )
        assert plan.is_incremental is True
        assert "reasoning_feature" in plan.affected_feature_type_ids

    def test_replay_plan(self) -> None:
        plan = _make_plan(is_replay=True, is_full_recomputation=True)
        assert plan.is_replay is True

    def test_empty_session_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_plan(session_id="")

    def test_negative_question_index_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_plan(current_question_index=-1)

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            _make_plan(unknown="x")

    def test_immutable(self) -> None:
        plan = _make_plan()
        with pytest.raises(ValidationError):
            plan.is_replay = True  # type: ignore[misc]

    def test_default_schema_version(self) -> None:
        assert _make_plan().schema_version == "1.0"
