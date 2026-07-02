# tests/services/coaching_engine/test_coaching_engine_failure.py
# Failure handling tests: CoachingEngine never raises

import pytest
from unittest.mock import MagicMock, patch

from services.coaching_engine.coaching_engine import CoachingEngine
from services.coaching_engine.coaching_diagnostics import CoachingStage


class TestCoachingEngineFailureHandling:
    @pytest.fixture(autouse=True)
    def engine(self) -> CoachingEngine:
        self._engine = CoachingEngine()

    def test_never_raises_on_valid_input(self, base_context):
        result = self._engine.run(base_context)
        assert result is not None

    def test_never_raises_on_empty_input(self, empty_context):
        result = self._engine.run(empty_context)
        assert result is not None

    def test_gap_analysis_exception_returns_failure_result(self, base_context):
        with patch.object(
            self._engine,
            "_run_gap_analysis",
            side_effect=Exception("injected gap analysis failure"),
        ):
            result = self._engine.run(base_context)
        assert result.is_successful is False
        assert result.failure_reason is not None

    def test_objective_derivation_exception_captured(self, base_context):
        with patch.object(
            self._engine,
            "_run_objective_derivation",
            side_effect=Exception("injected objective failure"),
        ):
            result = self._engine.run(base_context)
        assert result.is_successful is False

    def test_action_derivation_exception_captured(self, base_context):
        with patch.object(
            self._engine,
            "_run_action_derivation",
            side_effect=Exception("injected action failure"),
        ):
            result = self._engine.run(base_context)
        assert result.is_successful is False

    def test_recommendation_derivation_exception_captured(self, base_context):
        with patch.object(
            self._engine,
            "_run_recommendation_derivation",
            side_effect=Exception("injected recommendation failure"),
        ):
            result = self._engine.run(base_context)
        assert result.is_successful is False

    def test_plan_assembly_exception_returns_empty_snapshot(self, base_context):
        with patch.object(
            self._engine,
            "_run_plan_assembly",
            side_effect=Exception("injected assembly failure"),
        ):
            result = self._engine.run(base_context)
        assert result.is_successful is False
        assert result.snapshot is not None
        assert result.snapshot.statistics.is_empty

    def test_failure_result_has_diagnostics(self, base_context):
        with patch.object(
            self._engine,
            "_run_gap_analysis",
            side_effect=Exception("forced failure"),
        ):
            result = self._engine.run(base_context)
        assert result.diagnostics is not None
        assert result.diagnostics.is_successful is False

    def test_failure_result_has_failure_reason(self, base_context):
        with patch.object(
            self._engine,
            "_run_objective_derivation",
            side_effect=Exception("specific error"),
        ):
            result = self._engine.run(base_context)
        assert result.failure_reason is not None
        assert len(result.failure_reason) > 0
