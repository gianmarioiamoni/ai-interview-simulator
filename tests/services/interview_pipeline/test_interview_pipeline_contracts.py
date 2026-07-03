# tests/services/interview_pipeline/test_interview_pipeline_contracts.py
# Contract tests: context, configuration, metrics, diagnostics, result

from __future__ import annotations

import pytest

from services.interview_pipeline.interview_pipeline_configuration import (
    InterviewPipelineConfiguration,
)
from services.interview_pipeline.interview_pipeline_context import InterviewPipelineContext
from services.interview_pipeline.interview_pipeline_diagnostics import (
    InterviewPipelineDiagnostics,
    InterviewPipelineStage,
    StageAuditRecord,
)
from services.interview_pipeline.interview_pipeline_metrics import InterviewPipelineMetrics
from services.interview_pipeline.interview_pipeline_result import InterviewPipelineResult
from tests.services.interview_pipeline.conftest import (
    CAND,
    Q_IDX,
    SESSION,
    make_candidate_profile,
    make_context,
)


class TestInterviewPipelineContext:
    def test_minimal_context_is_valid(self):
        ctx = make_context()
        assert ctx.session_id == SESSION
        assert ctx.candidate_identity_id == CAND
        assert ctx.question_index == Q_IDX

    def test_context_is_frozen(self):
        ctx = make_context()
        with pytest.raises(Exception):
            ctx.session_id = "mutated"  # type: ignore[misc]

    def test_context_requires_session_id(self):
        with pytest.raises(Exception):
            InterviewPipelineContext(
                session_id="",
                candidate_identity_id=CAND,
                question_index=Q_IDX,
            )

    def test_context_requires_candidate_id(self):
        with pytest.raises(Exception):
            InterviewPipelineContext(
                session_id=SESSION,
                candidate_identity_id="",
                question_index=Q_IDX,
            )

    def test_context_rejects_negative_question_index(self):
        with pytest.raises(Exception):
            InterviewPipelineContext(
                session_id=SESSION,
                candidate_identity_id=CAND,
                question_index=-1,
            )

    def test_context_allows_zero_question_index(self):
        ctx = InterviewPipelineContext(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=0,
        )
        assert ctx.question_index == 0

    def test_context_optional_fields_default(self):
        ctx = InterviewPipelineContext(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=0,
        )
        assert ctx.signals == ()
        assert ctx.prior_profile is None
        assert ctx.interview_topic is None
        assert ctx.interview_role is None
        assert ctx.knowledge_gap_observation_ids == ()
        assert ctx.evaluation_summary == {}
        assert ctx.interview_metadata == {}


class TestInterviewPipelineConfiguration:
    def test_default_configuration_is_valid(self):
        config = InterviewPipelineConfiguration()
        assert config.pipeline_version == "1.0.0"
        assert config.abort_on_knowledge_pipeline_failure is True
        assert config.abort_on_narrative_failure is False
        assert config.abort_on_coaching_failure is False
        assert config.abort_on_session_close_failure is False

    def test_configuration_composes_knowledge_pipeline_config(self):
        config = InterviewPipelineConfiguration()
        assert config.knowledge_pipeline_configuration is not None

    def test_configuration_composes_session_close_config(self):
        config = InterviewPipelineConfiguration()
        assert config.session_close_configuration is not None

    def test_configuration_is_frozen(self):
        config = InterviewPipelineConfiguration()
        with pytest.raises(Exception):
            config.pipeline_version = "mutated"  # type: ignore[misc]


class TestInterviewPipelineMetrics:
    def test_default_metrics_are_zero(self):
        m = InterviewPipelineMetrics(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=Q_IDX,
        )
        assert m.knowledge_pipeline_duration_ms == 0.0
        assert m.narrative_generator_duration_ms == 0.0
        assert m.coaching_engine_duration_ms == 0.0
        assert m.session_close_duration_ms == 0.0
        assert m.total_duration_ms == 0.0
        assert m.signals_received == 0
        assert m.features_produced == 0

    def test_metrics_is_frozen(self):
        m = InterviewPipelineMetrics(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=Q_IDX,
        )
        with pytest.raises(Exception):
            m.total_duration_ms = 999.0  # type: ignore[misc]


class TestInterviewPipelineDiagnosticsFactories:
    def _metrics(self) -> InterviewPipelineMetrics:
        return InterviewPipelineMetrics(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=Q_IDX,
        )

    def test_successful_factory(self):
        d = InterviewPipelineDiagnostics.successful(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=Q_IDX,
            stage_records=(),
            metrics=self._metrics(),
        )
        assert d.is_successful is True
        assert d.failure_stage is None
        assert d.failure_reason is None

    def test_failed_factory(self):
        d = InterviewPipelineDiagnostics.failed(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=Q_IDX,
            stage_records=(),
            metrics=self._metrics(),
            failure_stage=InterviewPipelineStage.KNOWLEDGE_PIPELINE,
            failure_reason="test failure",
        )
        assert d.is_successful is False
        assert d.failure_stage == InterviewPipelineStage.KNOWLEDGE_PIPELINE
        assert d.failure_reason == "test failure"


class TestInterviewPipelineResult:
    def _metrics(self) -> InterviewPipelineMetrics:
        return InterviewPipelineMetrics(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=Q_IDX,
        )

    def _diag(self) -> InterviewPipelineDiagnostics:
        return InterviewPipelineDiagnostics.successful(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=Q_IDX,
            stage_records=(),
            metrics=self._metrics(),
        )

    def test_result_with_all_none_outputs(self):
        r = InterviewPipelineResult(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=Q_IDX,
            diagnostics=self._diag(),
        )
        assert r.has_profile is False
        assert r.has_narrative is False
        assert r.has_coaching is False
        assert r.has_session_history is False

    def test_result_is_frozen(self):
        r = InterviewPipelineResult(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=Q_IDX,
            diagnostics=self._diag(),
        )
        with pytest.raises(Exception):
            r.is_successful = False  # type: ignore[misc]

    def test_stages_completed_counts_completed_records(self):
        records = (
            StageAuditRecord(stage=InterviewPipelineStage.KNOWLEDGE_PIPELINE, completed=True, duration_ms=0.0),
            StageAuditRecord(stage=InterviewPipelineStage.NARRATIVE_GENERATOR, completed=True, duration_ms=0.0),
            StageAuditRecord(stage=InterviewPipelineStage.COACHING_ENGINE, completed=False, duration_ms=0.0),
        )
        diag = InterviewPipelineDiagnostics.successful(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=Q_IDX,
            stage_records=records,
            metrics=self._metrics(),
        )
        r = InterviewPipelineResult(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=Q_IDX,
            diagnostics=diag,
        )
        assert r.stages_completed == 2
