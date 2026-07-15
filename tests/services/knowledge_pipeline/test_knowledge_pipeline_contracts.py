# tests/services/knowledge_pipeline/test_knowledge_pipeline_contracts.py
# Contract tests: shape, immutability, and invariants of pipeline types

import pytest
from pydantic import ValidationError

from services.knowledge_pipeline.knowledge_pipeline_configuration import (
    KnowledgePipelineConfiguration,
)
from services.knowledge_pipeline.knowledge_pipeline_context import KnowledgePipelineContext
from services.knowledge_pipeline.knowledge_pipeline_diagnostics import (
    KnowledgePipelineDiagnostics,
    PipelineStage,
    StageAuditRecord,
)
from services.knowledge_pipeline.knowledge_pipeline_metrics import KnowledgePipelineMetrics
from services.knowledge_pipeline.knowledge_pipeline_result import KnowledgePipelineResult
from tests.services.knowledge_pipeline.conftest import make_signal


class TestKnowledgePipelineConfiguration:
    def test_defaults(self):
        cfg = KnowledgePipelineConfiguration()
        assert cfg.pipeline_version == "1.0.0"
        assert cfg.abort_on_stage_failure is False
        assert cfg.allow_empty_signal_cycles is False

    def test_frozen(self):
        cfg = KnowledgePipelineConfiguration()
        with pytest.raises(Exception):
            cfg.pipeline_version = "mutated"  # type: ignore[misc]

    def test_custom_values(self):
        cfg = KnowledgePipelineConfiguration(
            abort_on_stage_failure=True,
            extractor_version="2.0",
            feature_engine_version="2.0.0",
        )
        assert cfg.abort_on_stage_failure is True
        assert cfg.extractor_version == "2.0"


class TestKnowledgePipelineContext:
    def test_minimal_valid(self):
        ctx = KnowledgePipelineContext(
            session_id="sess-001",
            candidate_identity_id="cand-001",
            question_index=0,
        )
        assert ctx.signals == ()
        assert ctx.prior_profile is None

    def test_with_signals(self):
        sig = make_signal()
        ctx = KnowledgePipelineContext(
            session_id="sess-001",
            candidate_identity_id="cand-001",
            question_index=0,
            signals=(sig,),
        )
        assert len(ctx.signals) == 1

    def test_negative_question_index_rejected(self):
        with pytest.raises(ValidationError):
            KnowledgePipelineContext(
                session_id="sess-001",
                candidate_identity_id="cand-001",
                question_index=-1,
            )

    def test_empty_session_id_rejected(self):
        with pytest.raises(ValidationError):
            KnowledgePipelineContext(
                session_id="",
                candidate_identity_id="cand-001",
                question_index=0,
            )

    def test_frozen(self):
        ctx = KnowledgePipelineContext(
            session_id="sess-001",
            candidate_identity_id="cand-001",
            question_index=0,
        )
        with pytest.raises(Exception):
            ctx.question_index = 1  # type: ignore[misc]


class TestKnowledgePipelineMetrics:
    def test_defaults(self):
        m = KnowledgePipelineMetrics(
            session_id="sess-001",
            candidate_identity_id="cand-001",
            question_index=0,
        )
        assert m.signals_received == 0
        assert m.observations_produced == 0
        assert m.features_computed == 0
        assert m.total_duration_ms == 0.0

    def test_non_negative_enforced(self):
        with pytest.raises(ValidationError):
            KnowledgePipelineMetrics(
                session_id="sess-001",
                candidate_identity_id="cand-001",
                question_index=0,
                signals_received=-1,
            )


class TestStageAuditRecord:
    def test_completed(self):
        rec = StageAuditRecord(stage=PipelineStage.EXTRACTION, completed=True, duration_ms=5.0)
        assert rec.completed is True
        assert rec.error_message is None

    def test_failed(self):
        rec = StageAuditRecord(
            stage=PipelineStage.FEATURE_ENGINE,
            completed=False,
            error_message="oops",
        )
        assert rec.completed is False
        assert rec.error_message == "oops"


class TestKnowledgePipelineDiagnostics:
    def _metrics(self) -> KnowledgePipelineMetrics:
        return KnowledgePipelineMetrics(session_id="s", candidate_identity_id="c", question_index=0)

    def test_successful_factory(self):
        diag = KnowledgePipelineDiagnostics.successful(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
            stage_records=(),
            metrics=self._metrics(),
        )
        assert diag.is_successful is True
        assert diag.failure_stage is None
        assert diag.failure_reason is None

    def test_failed_factory(self):
        diag = KnowledgePipelineDiagnostics.failed(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
            stage_records=(),
            metrics=self._metrics(),
            failure_stage=PipelineStage.EXTRACTION,
            failure_reason="no signals",
        )
        assert diag.is_successful is False
        assert diag.failure_stage == PipelineStage.EXTRACTION
        assert diag.failure_reason == "no signals"


class TestKnowledgePipelineResult:
    def _diag(self) -> KnowledgePipelineDiagnostics:
        m = KnowledgePipelineMetrics(session_id="s", candidate_identity_id="c", question_index=0)
        return KnowledgePipelineDiagnostics.successful(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
            stage_records=(),
            metrics=m,
        )

    def test_successful_result(self):
        r = KnowledgePipelineResult(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
            diagnostics=self._diag(),
            is_successful=True,
        )
        assert r.has_profile is False
        assert r.feature_count == 0

    def test_feature_count_property(self):
        r = KnowledgePipelineResult(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
            diagnostics=self._diag(),
        )
        assert r.feature_count == 0
