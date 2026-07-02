# tests/services/coaching_engine/test_coaching_contracts.py
# Contract tests: CoachingContext, CoachingResult, CoachingMetrics, CoachingDiagnostics

import pytest
from pydantic import ValidationError

from domain.contracts.coaching.coaching_builder import CoachingBuilder
from services.coaching_engine.coaching_context import CoachingContext
from services.coaching_engine.coaching_diagnostics import (
    CoachingDiagnostics,
    CoachingStage,
    CoachingStageRecord,
)
from services.coaching_engine.coaching_metrics import CoachingMetrics
from services.coaching_engine.coaching_result import CoachingResult


# ---------------------------------------------------------------------------
# CoachingContext
# ---------------------------------------------------------------------------


class TestCoachingContext:
    def test_minimal_valid_context(self, candidate_profile):
        ctx = CoachingContext(
            session_id="s1",
            candidate_identity_id="c1",
            question_index=0,
            profile=candidate_profile,
        )
        assert ctx.session_id == "s1"
        assert ctx.question_index == 0
        assert ctx.features == ()
        assert ctx.knowledge_gap_observation_ids == ()

    def test_immutable(self, base_context):
        with pytest.raises((ValidationError, TypeError)):
            base_context.session_id = "mutated"

    def test_rejects_empty_session_id(self, candidate_profile):
        with pytest.raises(ValidationError):
            CoachingContext(
                session_id="",
                candidate_identity_id="c1",
                question_index=0,
                profile=candidate_profile,
            )

    def test_rejects_negative_question_index(self, candidate_profile):
        with pytest.raises(ValidationError):
            CoachingContext(
                session_id="s1",
                candidate_identity_id="c1",
                question_index=-1,
                profile=candidate_profile,
            )

    def test_optional_fields_default_to_none(self, candidate_profile):
        ctx = CoachingContext(
            session_id="s1",
            candidate_identity_id="c1",
            question_index=0,
            profile=candidate_profile,
        )
        assert ctx.learning_progress_summary is None
        assert ctx.language_profile is None
        assert ctx.interview_topic is None
        assert ctx.interview_role is None
        assert ctx.prior_coaching_snapshot is None


# ---------------------------------------------------------------------------
# CoachingMetrics
# ---------------------------------------------------------------------------


class TestCoachingMetrics:
    def test_defaults(self):
        m = CoachingMetrics(
            session_id="s1",
            candidate_identity_id="c1",
            question_index=0,
        )
        assert m.total_duration_ms == 0.0
        assert m.objectives_produced == 0

    def test_rejects_negative_duration(self):
        with pytest.raises(ValidationError):
            CoachingMetrics(
                session_id="s1",
                candidate_identity_id="c1",
                question_index=0,
                total_duration_ms=-1.0,
            )

    def test_immutable(self):
        m = CoachingMetrics(session_id="s1", candidate_identity_id="c1", question_index=0)
        with pytest.raises((ValidationError, TypeError)):
            m.total_duration_ms = 99.0


# ---------------------------------------------------------------------------
# CoachingStageRecord / CoachingDiagnostics
# ---------------------------------------------------------------------------


class TestCoachingDiagnostics:
    def _make_metrics(self, session_id: str = "s1") -> CoachingMetrics:
        return CoachingMetrics(
            session_id=session_id,
            candidate_identity_id="c1",
            question_index=0,
        )

    def test_successful_factory(self):
        metrics = self._make_metrics()
        diag = CoachingDiagnostics.successful(
            session_id="s1",
            candidate_identity_id="c1",
            question_index=0,
            stage_records=(),
            metrics=metrics,
        )
        assert diag.is_successful is True
        assert diag.failure_stage is None
        assert diag.failure_reason is None

    def test_failed_factory(self):
        metrics = self._make_metrics()
        diag = CoachingDiagnostics.failed(
            session_id="s1",
            candidate_identity_id="c1",
            question_index=0,
            stage_records=(),
            metrics=metrics,
            failure_stage=CoachingStage.GAP_ANALYSIS,
            failure_reason="test failure",
        )
        assert diag.is_successful is False
        assert diag.failure_stage == CoachingStage.GAP_ANALYSIS
        assert diag.failure_reason == "test failure"

    def test_stage_record_immutable(self):
        record = CoachingStageRecord(stage=CoachingStage.GAP_ANALYSIS, completed=True)
        with pytest.raises((ValidationError, TypeError)):
            record.completed = False


# ---------------------------------------------------------------------------
# CoachingResult
# ---------------------------------------------------------------------------


class TestCoachingResult:
    def _make_result(self, is_successful: bool = True) -> CoachingResult:
        snapshot = CoachingBuilder.empty(session_id="s1", question_index=0)
        metrics = CoachingMetrics(session_id="s1", candidate_identity_id="c1", question_index=0)
        diagnostics = CoachingDiagnostics.successful(
            session_id="s1",
            candidate_identity_id="c1",
            question_index=0,
            stage_records=(),
            metrics=metrics,
        )
        return CoachingResult(
            session_id="s1",
            candidate_identity_id="c1",
            question_index=0,
            snapshot=snapshot,
            diagnostics=diagnostics,
            is_successful=is_successful,
        )

    def test_has_objectives_false_on_empty(self):
        result = self._make_result()
        assert result.has_objectives is False
        assert result.objective_count == 0

    def test_immutable(self):
        result = self._make_result()
        with pytest.raises((ValidationError, TypeError)):
            result.is_successful = False
