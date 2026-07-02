# services/knowledge_pipeline/knowledge_pipeline.py
# KnowledgePipeline — end-to-end orchestration (E02-M5 / E01-M6)
#
# Pipeline stages:
#   EvidenceSignal → ObservationExtractor → ObservationBatch → ObservationStore
#   → ObservationStoreQueryEngine → FeatureEngine → FeatureBatch
#   → CandidateProfileBuilder → CandidateProfile
#
# Invariants (ADR-016, ADR-018, ADR-020, ADR-037):
# - No business logic here; all computation is delegated to domain components.
# - No LLM, Narrative, Coaching, Replay, SessionHistory, Persistence.
# - Deterministic: same inputs produce the same output.

from __future__ import annotations

import time

from domain.contracts.observation.extraction.observation_extraction_context import (
    ObservationExtractionContext,
)
from domain.contracts.observation.extraction.observation_extractor import ObservationExtractor
from domain.contracts.observation.observation_store import ObservationStore
from domain.observation.runtime.observation_store_query_engine import ObservationStoreQueryEngine
from domain.profile.candidate_profile_builder import CandidateProfileBuilder
from services.feature_engine.feature_engine import FeatureEngine
from services.feature_engine.feature_engine_context import FeatureEngineContext
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


class KnowledgePipeline:
    """Orchestrates the end-to-end Knowledge Pipeline (E02-M5 / E01-M6).

    Delegates all knowledge computation to:
    - ObservationExtractor  (extraction stage)
    - ObservationStore      (append stage)
    - ObservationStoreQueryEngine (query stage)
    - FeatureEngine         (feature computation stage)
    - CandidateProfileBuilder (profile build stage)

    This class owns ONLY orchestration: stage sequencing, error propagation,
    metric collection, and result assembly.

    No business logic is implemented here.
    """

    def __init__(
        self,
        extractor: ObservationExtractor,
        store: ObservationStore,
        query_engine: ObservationStoreQueryEngine,
        feature_engine: FeatureEngine,
        configuration: KnowledgePipelineConfiguration | None = None,
    ) -> None:
        self._extractor = extractor
        self._store = store
        self._query_engine = query_engine
        self._feature_engine = feature_engine
        self._configuration = configuration or KnowledgePipelineConfiguration()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, context: KnowledgePipelineContext) -> KnowledgePipelineResult:
        """Execute one full pipeline cycle for the given context.

        Returns KnowledgePipelineResult regardless of success/failure.
        Never raises; errors are captured in the result's diagnostics.
        """
        cycle_start = time.monotonic()
        stage_records: list[StageAuditRecord] = []

        # Fast-path: empty signals when not allowed
        if not context.signals and not self._configuration.allow_empty_signal_cycles:
            metrics = self._build_metrics(
                context=context,
                signals_received=0,
                observations_produced=0,
                observations_in_store=0,
                features_computed=0,
                extraction_ms=0.0,
                store_ms=0.0,
                feature_ms=0.0,
                profile_ms=0.0,
                total_ms=(time.monotonic() - cycle_start) * 1000.0,
            )
            diagnostics = KnowledgePipelineDiagnostics.failed(
                session_id=context.session_id,
                candidate_identity_id=context.candidate_identity_id,
                question_index=context.question_index,
                stage_records=tuple(stage_records),
                metrics=metrics,
                failure_stage=PipelineStage.EXTRACTION,
                failure_reason="No EvidenceSignals provided and allow_empty_signal_cycles is False.",
            )
            return KnowledgePipelineResult(
                session_id=context.session_id,
                candidate_identity_id=context.candidate_identity_id,
                question_index=context.question_index,
                diagnostics=diagnostics,
                is_successful=False,
                failure_reason=diagnostics.failure_reason,
            )

        # --- Stage 1: Extraction ---
        t0 = time.monotonic()
        extraction_result, extraction_record = self._run_extraction(context)
        extraction_ms = (time.monotonic() - t0) * 1000.0
        stage_records.append(extraction_record)

        if not extraction_record.completed and self._configuration.abort_on_stage_failure:
            return self._abort(
                context=context,
                stage_records=stage_records,
                failure_stage=PipelineStage.EXTRACTION,
                failure_reason=extraction_record.error_message or "Extraction failed.",
                cycle_start=cycle_start,
                signals_received=len(context.signals),
                observations_produced=0,
                observations_in_store=0,
                features_computed=0,
                extraction_ms=extraction_ms,
                store_ms=0.0,
                feature_ms=0.0,
                profile_ms=0.0,
            )

        observations_produced = (
            len(extraction_result.observations) if extraction_result is not None else 0
        )

        # --- Stage 2: ObservationBatch → ObservationStore (append) ---
        # ObservationExtractor already appended to store during extract().
        # We record a no-op store_append stage for audit completeness.
        t1 = time.monotonic()
        store_record = StageAuditRecord(
            stage=PipelineStage.STORE_APPEND,
            completed=True,
            duration_ms=(time.monotonic() - t1) * 1000.0,
        )
        store_ms = (time.monotonic() - t1) * 1000.0
        stage_records.append(store_record)

        observations_in_store = self._store.count()

        # --- Stage 3: ObservationStoreQueryEngine (snapshot) ---
        t2 = time.monotonic()
        snapshot = self._store.snapshot()
        query_record = StageAuditRecord(
            stage=PipelineStage.QUERY_ENGINE,
            completed=True,
            duration_ms=(time.monotonic() - t2) * 1000.0,
        )
        stage_records.append(query_record)

        # --- Stage 4: FeatureEngine ---
        t3 = time.monotonic()
        feature_result, feature_record = self._run_feature_engine(context, snapshot)
        feature_ms = (time.monotonic() - t3) * 1000.0
        stage_records.append(feature_record)

        if not feature_record.completed and self._configuration.abort_on_stage_failure:
            return self._abort(
                context=context,
                stage_records=stage_records,
                failure_stage=PipelineStage.FEATURE_ENGINE,
                failure_reason=feature_record.error_message or "FeatureEngine failed.",
                cycle_start=cycle_start,
                signals_received=len(context.signals),
                observations_produced=observations_produced,
                observations_in_store=observations_in_store,
                features_computed=0,
                extraction_ms=extraction_ms,
                store_ms=store_ms,
                feature_ms=feature_ms,
                profile_ms=0.0,
            )

        features = feature_result.features if feature_result is not None else ()
        features_computed = len(features)

        # --- Stage 5: CandidateProfileBuilder ---
        t4 = time.monotonic()
        profile, profile_record = self._run_profile_build(context, features)
        profile_ms = (time.monotonic() - t4) * 1000.0
        stage_records.append(profile_record)

        if not profile_record.completed and self._configuration.abort_on_stage_failure:
            return self._abort(
                context=context,
                stage_records=stage_records,
                failure_stage=PipelineStage.PROFILE_BUILD,
                failure_reason=profile_record.error_message or "Profile build failed.",
                cycle_start=cycle_start,
                signals_received=len(context.signals),
                observations_produced=observations_produced,
                observations_in_store=observations_in_store,
                features_computed=features_computed,
                extraction_ms=extraction_ms,
                store_ms=store_ms,
                feature_ms=feature_ms,
                profile_ms=profile_ms,
            )

        total_ms = (time.monotonic() - cycle_start) * 1000.0
        metrics = self._build_metrics(
            context=context,
            signals_received=len(context.signals),
            observations_produced=observations_produced,
            observations_in_store=observations_in_store,
            features_computed=features_computed,
            extraction_ms=extraction_ms,
            store_ms=store_ms,
            feature_ms=feature_ms,
            profile_ms=profile_ms,
            total_ms=total_ms,
        )
        diagnostics = KnowledgePipelineDiagnostics.successful(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            stage_records=tuple(stage_records),
            metrics=metrics,
        )
        return KnowledgePipelineResult(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            profile=profile,
            features=features,
            diagnostics=diagnostics,
            is_successful=True,
        )

    # ------------------------------------------------------------------
    # Stage runners
    # ------------------------------------------------------------------

    def _run_extraction(
        self,
        context: KnowledgePipelineContext,
    ) -> tuple:
        """Run ObservationExtractor. Returns (result | None, StageAuditRecord)."""
        t0 = time.monotonic()
        try:
            extraction_context = ObservationExtractionContext(
                signals=context.signals,
                question_index=context.question_index,
                session_id=context.session_id,
                extractor_version=self._configuration.extractor_version,
            )
            result = self._extractor.extract(extraction_context)
            duration_ms = (time.monotonic() - t0) * 1000.0
            return result, StageAuditRecord(
                stage=PipelineStage.EXTRACTION,
                completed=True,
                duration_ms=duration_ms,
            )
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.monotonic() - t0) * 1000.0
            return None, StageAuditRecord(
                stage=PipelineStage.EXTRACTION,
                completed=False,
                error_message=str(exc),
                duration_ms=duration_ms,
            )

    def _run_feature_engine(
        self,
        context: KnowledgePipelineContext,
        snapshot,
    ) -> tuple:
        """Run FeatureEngine. Returns (result | None, StageAuditRecord)."""
        t0 = time.monotonic()
        try:
            engine_context = FeatureEngineContext(
                session_id=context.session_id,
                candidate_identity_id=context.candidate_identity_id,
                current_question_index=context.question_index,
                snapshot=snapshot,
                feature_engine_version=self._configuration.feature_engine_version,
                is_replay=False,
            )
            result = self._feature_engine.run(engine_context)
            duration_ms = (time.monotonic() - t0) * 1000.0
            return result, StageAuditRecord(
                stage=PipelineStage.FEATURE_ENGINE,
                completed=True,
                duration_ms=duration_ms,
            )
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.monotonic() - t0) * 1000.0
            return None, StageAuditRecord(
                stage=PipelineStage.FEATURE_ENGINE,
                completed=False,
                error_message=str(exc),
                duration_ms=duration_ms,
            )

    def _run_profile_build(
        self,
        context: KnowledgePipelineContext,
        features: tuple,
    ) -> tuple:
        """Run CandidateProfileBuilder. Returns (profile | None, StageAuditRecord)."""
        t0 = time.monotonic()
        try:
            if context.prior_profile is not None:
                builder = CandidateProfileBuilder.from_profile(context.prior_profile)
            else:
                builder = CandidateProfileBuilder()

            profile = (
                builder
                .with_questions_answered(context.question_index + 1)
                .with_last_updated_at(context.question_index)
                .build()
            )
            duration_ms = (time.monotonic() - t0) * 1000.0
            return profile, StageAuditRecord(
                stage=PipelineStage.PROFILE_BUILD,
                completed=True,
                duration_ms=duration_ms,
            )
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.monotonic() - t0) * 1000.0
            return None, StageAuditRecord(
                stage=PipelineStage.PROFILE_BUILD,
                completed=False,
                error_message=str(exc),
                duration_ms=duration_ms,
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _abort(
        self,
        context: KnowledgePipelineContext,
        stage_records: list[StageAuditRecord],
        failure_stage: PipelineStage,
        failure_reason: str,
        cycle_start: float,
        signals_received: int,
        observations_produced: int,
        observations_in_store: int,
        features_computed: int,
        extraction_ms: float,
        store_ms: float,
        feature_ms: float,
        profile_ms: float,
    ) -> KnowledgePipelineResult:
        total_ms = (time.monotonic() - cycle_start) * 1000.0
        metrics = self._build_metrics(
            context=context,
            signals_received=signals_received,
            observations_produced=observations_produced,
            observations_in_store=observations_in_store,
            features_computed=features_computed,
            extraction_ms=extraction_ms,
            store_ms=store_ms,
            feature_ms=feature_ms,
            profile_ms=profile_ms,
            total_ms=total_ms,
        )
        diagnostics = KnowledgePipelineDiagnostics.failed(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            stage_records=tuple(stage_records),
            metrics=metrics,
            failure_stage=failure_stage,
            failure_reason=failure_reason,
        )
        return KnowledgePipelineResult(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            diagnostics=diagnostics,
            is_successful=False,
            failure_reason=failure_reason,
        )

    def _build_metrics(
        self,
        context: KnowledgePipelineContext,
        signals_received: int,
        observations_produced: int,
        observations_in_store: int,
        features_computed: int,
        extraction_ms: float,
        store_ms: float,
        feature_ms: float,
        profile_ms: float,
        total_ms: float,
    ) -> KnowledgePipelineMetrics:
        return KnowledgePipelineMetrics(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            extraction_duration_ms=extraction_ms,
            store_append_duration_ms=store_ms,
            feature_engine_duration_ms=feature_ms,
            profile_build_duration_ms=profile_ms,
            total_duration_ms=total_ms,
            signals_received=signals_received,
            observations_produced=observations_produced,
            observations_in_store=observations_in_store,
            features_computed=features_computed,
        )
