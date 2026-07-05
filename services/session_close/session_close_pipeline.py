# services/session_close/session_close_pipeline.py
# SessionClosePipeline — orchestration layer for session close (ADR-022 §E, ADR-032)

from __future__ import annotations

import time
from typing import Optional

from domain.contracts.session_history.session_history import ReplayMetadata
from domain.contracts.session_history.session_history_builder import SessionHistoryBuilder
from services.session_close.session_close_configuration import SessionCloseConfiguration
from services.session_close.session_close_context import SessionCloseContext
from services.session_close.session_close_diagnostics import SessionCloseDiagnostics
from services.session_close.session_close_metrics import SessionCloseMetrics
from services.session_close.session_close_result import SessionCloseResult


class SessionClosePipelineError(Exception):
    """Raised when SessionClosePipeline encounters an unrecoverable orchestration error."""


class SessionClosePipeline:
    """Orchestration layer that closes an interview session (ADR-022 §E, ADR-032).

    Responsibilities (orchestration only):
    1. Validate context identity consistency.
    2. Assemble SessionHistory via SessionHistoryBuilder.
    3. Return SessionCloseResult with diagnostics.

    Explicitly out of scope:
    - No persistence (caller decides).
    - No repository calls.
    - No FeatureEngine invocation (KnowledgeSnapshot already carries features).
    - No Narrative generation.
    - No Coaching generation.
    - No Replay pipeline.
    - No LearningProgress derivation.
    - No CandidateProfile mutation.

    CandidateProfileSnapshot ownership (ADR-032):
    The KnowledgeSnapshot passed in SessionCloseContext already contains the
    CandidateProfileSnapshot produced by FeatureEngine. This pipeline never
    creates a CandidateProfileSnapshot directly — it consumes the one embedded
    in KnowledgeSnapshot. FeatureEngine remains sole producer (ADR-032).

    Usage::

        pipeline = SessionClosePipeline()
        result = pipeline.run(context)
        if result.is_successful:
            persist(result.session_history)
    """

    def __init__(
        self,
        configuration: Optional[SessionCloseConfiguration] = None,
    ) -> None:
        self._config = configuration or SessionCloseConfiguration()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, context: SessionCloseContext) -> SessionCloseResult:
        """Execute the session close pipeline.

        Returns SessionCloseResult. Never raises — errors are captured in result.
        """
        t_start = time.monotonic()
        stages_completed: list[str] = []

        try:
            self._validate_context(context)
            stages_completed.append("validate")

            t_snap = time.monotonic()
            # KnowledgeSnapshot already assembled upstream — no work to do here.
            # This stage is a verification-only checkpoint.
            self._assert_snapshot_identity(context)
            snapshot_ms = (time.monotonic() - t_snap) * 1000.0
            stages_completed.append("snapshot")

            t_hist = time.monotonic()
            session_history = self._assemble_session_history(context)
            history_ms = (time.monotonic() - t_hist) * 1000.0
            stages_completed.append("history")

            total_ms = (time.monotonic() - t_start) * 1000.0

            metrics = SessionCloseMetrics(
                session_id=context.session_id,
                total_elapsed_ms=total_ms,
                snapshot_assembly_ms=snapshot_ms,
                history_assembly_ms=history_ms,
                transcript_entry_count=len(context.transcript),
                timeline_entry_count=len(context.question_timeline),
                feature_count=context.knowledge_snapshot.feature_count,
            )
            diagnostics = SessionCloseDiagnostics(
                session_id=context.session_id,
                candidate_identity_id=context.candidate_identity_id,
                interview_index=context.interview_index,
                is_successful=True,
                stages_completed=tuple(stages_completed),
                metrics=metrics,
            )
            return SessionCloseResult(
                session_id=context.session_id,
                candidate_identity_id=context.candidate_identity_id,
                is_successful=True,
                session_history=session_history,
                diagnostics=diagnostics,
            )

        except Exception as exc:
            total_ms = (time.monotonic() - t_start) * 1000.0
            failure_stage = _last_or_unknown(stages_completed)
            failure_reason = str(exc)
            metrics = SessionCloseMetrics(
                session_id=context.session_id,
                total_elapsed_ms=total_ms,
            )
            diagnostics = SessionCloseDiagnostics(
                session_id=context.session_id,
                candidate_identity_id=context.candidate_identity_id,
                interview_index=context.interview_index,
                is_successful=False,
                stages_completed=tuple(stages_completed),
                failure_stage=failure_stage,
                failure_reason=failure_reason,
                metrics=metrics,
            )
            return SessionCloseResult(
                session_id=context.session_id,
                candidate_identity_id=context.candidate_identity_id,
                is_successful=False,
                session_history=None,
                diagnostics=diagnostics,
                failure_reason=failure_reason,
            )

    # ------------------------------------------------------------------
    # Private orchestration steps
    # ------------------------------------------------------------------

    def _validate_context(self, context: SessionCloseContext) -> None:
        if not context.session_id.strip():
            raise SessionClosePipelineError("session_id must not be blank.")
        if not context.candidate_identity_id.strip():
            raise SessionClosePipelineError("candidate_identity_id must not be blank.")
        if context.interview_index < 0:
            raise SessionClosePipelineError("interview_index must be >= 0.")

    def _assert_snapshot_identity(self, context: SessionCloseContext) -> None:
        snapshot = context.knowledge_snapshot
        if snapshot.candidate_identity_id != context.candidate_identity_id:
            raise SessionClosePipelineError(
                f"KnowledgeSnapshot.candidate_identity_id="
                f"'{snapshot.candidate_identity_id}' does not match context "
                f"candidate_identity_id='{context.candidate_identity_id}'."
            )
        if snapshot.session_id != context.session_id:
            raise SessionClosePipelineError(
                f"KnowledgeSnapshot.session_id='{snapshot.session_id}' "
                f"does not match context session_id='{context.session_id}'."
            )

    def _assemble_session_history(self, context: SessionCloseContext):
        replay_metadata = ReplayMetadata(
            snapshot_is_complete=self._config.replay_snapshot_is_complete,
            recomputation_available=self._config.recomputation_available,
            replay_schema_version=self._config.replay_schema_version,
        )

        builder = (
            SessionHistoryBuilder()
            .with_session_id(context.session_id)
            .with_candidate_identity_id(context.candidate_identity_id)
            .with_interview_index(context.interview_index)
            .with_knowledge_snapshot(context.knowledge_snapshot)
            .with_interview_metadata(context.interview_metadata)
            .with_language_profile(context.language_profile)
            .with_transcript(list(context.transcript))
            .with_question_timeline(list(context.question_timeline))
            .with_replay_metadata(replay_metadata)
            .with_schema_version(context.schema_version)
            .with_metadata(dict(context.metadata))
        )

        # Phase 7C (ADR-033): evaluation_result removed — new scoring artifacts only.
        if context.scoring_snapshot is not None:
            builder = builder.with_scoring_snapshot(context.scoring_snapshot)
        if context.scoring_narrative is not None:
            builder = builder.with_scoring_narrative(context.scoring_narrative)
        if context.question_results:
            builder = builder.with_question_results(list(context.question_results))
        if context.context_profile is not None:
            builder = builder.with_context_profile(context.context_profile)
        if context.generation_metadata is not None:
            builder = builder.with_generation_metadata(context.generation_metadata)

        return builder.build()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _last_or_unknown(stages: list[str]) -> str:
    return stages[-1] if stages else "unknown"
