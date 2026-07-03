# tests/services/session_close/test_session_close_pipeline.py
# Contract, validation, architecture, integration, and determinism tests

from __future__ import annotations

import pytest

from domain.contracts.session_history.session_history import SessionHistory
from services.session_close.session_close_configuration import SessionCloseConfiguration
from services.session_close.session_close_context import SessionCloseContext
from services.session_close.session_close_diagnostics import SessionCloseDiagnostics
from services.session_close.session_close_metrics import SessionCloseMetrics
from services.session_close.session_close_pipeline import SessionClosePipeline
from services.session_close.session_close_result import SessionCloseResult

from tests.domain.contracts.knowledge_snapshot.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    make_knowledge_snapshot,
)
from tests.domain.contracts.session_history.conftest import (
    make_language_profile,
    make_interview_metadata,
    make_transcript,
    make_question_timeline,
)
from tests.services.session_close.conftest import (
    INTERVIEW_INDEX,
    make_context,
)

CANDIDATE_ID_B = "cand-test-002"
SESSION_ID_B = "sess-test-002"


# ===========================================================================
# CONTRACT TESTS — SessionCloseContext
# ===========================================================================

class TestSessionCloseContext:
    def test_context_is_immutable(self, context: SessionCloseContext) -> None:
        with pytest.raises(Exception):
            context.session_id = "x"  # type: ignore[misc]

    def test_context_fields(self, context: SessionCloseContext) -> None:
        assert context.session_id == SESSION_ID
        assert context.candidate_identity_id == CANDIDATE_ID
        assert context.interview_index == INTERVIEW_INDEX

    def test_context_knowledge_snapshot_present(self, context: SessionCloseContext) -> None:
        assert context.knowledge_snapshot is not None
        assert context.knowledge_snapshot.session_id == SESSION_ID

    def test_context_transcript_and_timeline(self, context: SessionCloseContext) -> None:
        assert len(context.transcript) > 0
        assert len(context.question_timeline) > 0

    def test_context_default_close_reason(self, context: SessionCloseContext) -> None:
        assert context.close_reason == "normal"


# ===========================================================================
# CONTRACT TESTS — SessionCloseConfiguration
# ===========================================================================

class TestSessionCloseConfiguration:
    def test_default_config_is_immutable(self, default_config: SessionCloseConfiguration) -> None:
        with pytest.raises(Exception):
            default_config.replay_snapshot_is_complete = False  # type: ignore[misc]

    def test_default_replay_snapshot_is_complete(
        self, default_config: SessionCloseConfiguration
    ) -> None:
        assert default_config.replay_snapshot_is_complete is True

    def test_default_recomputation_available(
        self, default_config: SessionCloseConfiguration
    ) -> None:
        assert default_config.recomputation_available is False


# ===========================================================================
# CONTRACT TESTS — SessionCloseResult
# ===========================================================================

class TestSessionCloseResult:
    def test_result_is_immutable(self, pipeline: SessionClosePipeline, context: SessionCloseContext) -> None:
        result = pipeline.run(context)
        with pytest.raises(Exception):
            result.session_id = "x"  # type: ignore[misc]

    def test_successful_result_fields(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        assert result.is_successful
        assert result.session_id == SESSION_ID
        assert result.candidate_identity_id == CANDIDATE_ID
        assert result.failure_reason is None

    def test_successful_result_has_session_history(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        assert result.session_history is not None
        assert isinstance(result.session_history, SessionHistory)


# ===========================================================================
# CONTRACT TESTS — SessionCloseMetrics
# ===========================================================================

class TestSessionCloseMetrics:
    def test_metrics_is_immutable(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        with pytest.raises(Exception):
            result.diagnostics.metrics.total_elapsed_ms = 999.0  # type: ignore[misc]

    def test_metrics_session_id(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        assert result.diagnostics.metrics.session_id == SESSION_ID

    def test_metrics_transcript_count(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        assert result.diagnostics.metrics.transcript_entry_count == len(context.transcript)

    def test_metrics_timeline_count(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        assert result.diagnostics.metrics.timeline_entry_count == len(context.question_timeline)

    def test_metrics_feature_count(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        assert result.diagnostics.metrics.feature_count == context.knowledge_snapshot.feature_count


# ===========================================================================
# CONTRACT TESTS — SessionCloseDiagnostics
# ===========================================================================

class TestSessionCloseDiagnostics:
    def test_diagnostics_is_immutable(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        with pytest.raises(Exception):
            result.diagnostics.is_successful = False  # type: ignore[misc]

    def test_diagnostics_success_stages(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        assert result.diagnostics.is_successful
        assert "validate" in result.diagnostics.stages_completed
        assert "snapshot" in result.diagnostics.stages_completed
        assert "history" in result.diagnostics.stages_completed

    def test_diagnostics_stage_count(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        assert result.diagnostics.stage_count == 3


# ===========================================================================
# PIPELINE BEHAVIOUR TESTS
# ===========================================================================

class TestSessionClosePipelineSuccess:
    def test_pipeline_produces_session_history(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        assert result.is_successful
        sh = result.session_history
        assert sh is not None
        assert sh.session_id == SESSION_ID
        assert sh.candidate_identity_id == CANDIDATE_ID
        assert sh.interview_index == INTERVIEW_INDEX

    def test_pipeline_transcript_preserved(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        assert result.session_history is not None
        assert len(result.session_history.transcript) == len(context.transcript)

    def test_pipeline_timeline_preserved(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        assert result.session_history is not None
        assert len(result.session_history.question_timeline) == len(context.question_timeline)

    def test_pipeline_knowledge_snapshot_preserved(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        assert result.session_history is not None
        assert result.session_history.knowledge_snapshot.snapshot_id == \
               context.knowledge_snapshot.snapshot_id

    def test_pipeline_replay_metadata_from_config(self) -> None:
        config = SessionCloseConfiguration(
            replay_snapshot_is_complete=True,
            recomputation_available=False,
        )
        pipeline = SessionClosePipeline(configuration=config)
        result = pipeline.run(make_context())
        assert result.session_history is not None
        assert result.session_history.replay_metadata.snapshot_is_complete is True
        assert result.session_history.replay_metadata.recomputation_available is False

    def test_pipeline_never_raises(self) -> None:
        """Pipeline never raises — errors captured in result."""
        pipeline = SessionClosePipeline()
        bad_ks = make_knowledge_snapshot(session_id="wrong-session", candidate_id=CANDIDATE_ID)
        bad_context = SessionCloseContext(
            session_id=SESSION_ID,
            candidate_identity_id=CANDIDATE_ID,
            interview_index=0,
            knowledge_snapshot=bad_ks,
            interview_metadata=make_interview_metadata(),
            language_profile=make_language_profile(session_id=SESSION_ID),
        )
        result = pipeline.run(bad_context)
        assert not result.is_successful
        assert result.failure_reason is not None


class TestSessionClosePipelineFailure:
    def test_snapshot_session_id_mismatch_fails(self) -> None:
        ks = make_knowledge_snapshot(session_id="different-session", candidate_id=CANDIDATE_ID)
        context = SessionCloseContext(
            session_id=SESSION_ID,
            candidate_identity_id=CANDIDATE_ID,
            interview_index=0,
            knowledge_snapshot=ks,
            interview_metadata=make_interview_metadata(),
            language_profile=make_language_profile(session_id=SESSION_ID),
        )
        result = SessionClosePipeline().run(context)
        assert not result.is_successful
        assert "session_id" in (result.failure_reason or "").lower()

    def test_snapshot_candidate_mismatch_fails(self) -> None:
        ks = make_knowledge_snapshot(session_id=SESSION_ID, candidate_id=CANDIDATE_ID_B)
        context = SessionCloseContext(
            session_id=SESSION_ID,
            candidate_identity_id=CANDIDATE_ID,
            interview_index=0,
            knowledge_snapshot=ks,
            interview_metadata=make_interview_metadata(),
            language_profile=make_language_profile(session_id=SESSION_ID),
        )
        result = SessionClosePipeline().run(context)
        assert not result.is_successful

    def test_failure_result_has_no_session_history(self) -> None:
        ks = make_knowledge_snapshot(session_id="bad", candidate_id=CANDIDATE_ID)
        context = SessionCloseContext(
            session_id=SESSION_ID,
            candidate_identity_id=CANDIDATE_ID,
            interview_index=0,
            knowledge_snapshot=ks,
            interview_metadata=make_interview_metadata(),
            language_profile=make_language_profile(session_id=SESSION_ID),
        )
        result = SessionClosePipeline().run(context)
        assert result.session_history is None

    def test_failure_diagnostics_has_failure_stage(self) -> None:
        ks = make_knowledge_snapshot(session_id="bad", candidate_id=CANDIDATE_ID)
        context = SessionCloseContext(
            session_id=SESSION_ID,
            candidate_identity_id=CANDIDATE_ID,
            interview_index=0,
            knowledge_snapshot=ks,
            interview_metadata=make_interview_metadata(),
            language_profile=make_language_profile(session_id=SESSION_ID),
        )
        result = SessionClosePipeline().run(context)
        assert result.diagnostics.failure_stage is not None
        assert not result.diagnostics.is_successful


# ===========================================================================
# ARCHITECTURE TESTS
# ===========================================================================

class TestArchitectureInvariants:
    def test_pipeline_produces_no_persistence_artifact(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        """Result has no persistence ID, no DB reference."""
        result = pipeline.run(context)
        assert not hasattr(result, "persisted_at")
        assert not hasattr(result, "db_id")

    def test_profile_snapshot_comes_from_knowledge_snapshot(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        """CandidateProfileSnapshot is NOT created by pipeline — it comes from KnowledgeSnapshot."""
        result = pipeline.run(context)
        assert result.session_history is not None
        sh_snapshot = result.session_history.knowledge_snapshot
        assert sh_snapshot.snapshot_id == context.knowledge_snapshot.snapshot_id

    def test_pipeline_does_not_modify_context(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        original_session_id = context.session_id
        _ = pipeline.run(context)
        assert context.session_id == original_session_id

    def test_pipeline_does_not_modify_knowledge_snapshot(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        original_snapshot_id = context.knowledge_snapshot.snapshot_id
        _ = pipeline.run(context)
        assert context.knowledge_snapshot.snapshot_id == original_snapshot_id

    def test_no_replay_artifacts_in_result(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        assert not hasattr(result, "replay_result")
        assert not hasattr(result, "replay_session")

    def test_no_learning_progress_in_result(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        assert not hasattr(result, "learning_progress")

    def test_session_history_is_immutable(
        self, pipeline: SessionClosePipeline, context: SessionCloseContext
    ) -> None:
        result = pipeline.run(context)
        assert result.session_history is not None
        with pytest.raises(Exception):
            result.session_history.session_id = "x"  # type: ignore[misc]

    def test_feature_engine_not_called_by_pipeline(self) -> None:
        """Pipeline receives KnowledgeSnapshot; it does NOT invoke FeatureEngine."""
        ks = make_knowledge_snapshot(session_id=SESSION_ID, candidate_id=CANDIDATE_ID)
        ctx = make_context()
        assert ks.feature_count > 0
        result = SessionClosePipeline().run(ctx)
        assert result.is_successful
        assert result.session_history is not None
        assert result.session_history.knowledge_snapshot.feature_count == ks.feature_count


# ===========================================================================
# DETERMINISM TESTS
# ===========================================================================

class TestDeterminism:
    def test_same_context_same_session_id(self, pipeline: SessionClosePipeline) -> None:
        ctx = make_context()
        r1 = pipeline.run(ctx)
        r2 = pipeline.run(ctx)
        assert r1.session_id == r2.session_id

    def test_same_context_same_transcript_count(self, pipeline: SessionClosePipeline) -> None:
        ctx = make_context()
        r1 = pipeline.run(ctx)
        r2 = pipeline.run(ctx)
        assert r1.session_history is not None
        assert r2.session_history is not None
        assert len(r1.session_history.transcript) == len(r2.session_history.transcript)

    def test_same_context_same_feature_count(self, pipeline: SessionClosePipeline) -> None:
        ctx = make_context()
        r1 = pipeline.run(ctx)
        r2 = pipeline.run(ctx)
        assert r1.diagnostics.metrics.feature_count == r2.diagnostics.metrics.feature_count


# ===========================================================================
# INTEGRATION TESTS
# ===========================================================================

class TestIntegration:
    def test_full_pipeline_run_passes_validator(self) -> None:
        from domain.contracts.session_history.session_history_validator import (
            SessionHistoryValidator,
        )
        result = SessionClosePipeline().run(make_context())
        assert result.is_successful
        assert result.session_history is not None
        validation = SessionHistoryValidator.validate(result.session_history)
        assert validation.is_valid, validation.violations

    def test_pipeline_with_custom_config(self) -> None:
        config = SessionCloseConfiguration(recomputation_available=True)
        pipeline = SessionClosePipeline(configuration=config)
        result = pipeline.run(make_context())
        assert result.is_successful
        assert result.session_history is not None
        assert result.session_history.replay_metadata.recomputation_available is True

    def test_pipeline_result_carries_knowledge_epoch(self) -> None:
        result = SessionClosePipeline().run(make_context())
        assert result.session_history is not None
        assert result.session_history.knowledge_epoch == "1"

    def test_pipeline_metrics_non_negative(self) -> None:
        result = SessionClosePipeline().run(make_context())
        m = result.diagnostics.metrics
        assert m.total_elapsed_ms >= 0.0
        assert m.snapshot_assembly_ms >= 0.0
        assert m.history_assembly_ms >= 0.0
