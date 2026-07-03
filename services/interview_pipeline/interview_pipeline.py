# services/interview_pipeline/interview_pipeline.py
# InterviewPipeline — top-level orchestrator for the full interview pipeline
#
# Pipeline stages (in order):
#   InterviewPipelineContext
#   → KnowledgePipeline        (profile + features)
#   → NarrativeGenerator       (narrative)
#   → CoachingEngine           (coaching snapshot)
#   → SessionClosePipeline     (session history)
#   → InterviewPipelineResult
#
# Invariants:
# - Owns orchestration ONLY; no business logic implemented here.
# - Never computes ProfileFeatures.
# - Never generates Narrative directly.
# - Never creates Coaching objects.
# - Never builds SessionHistory directly.
# - Never invokes Replay.
# - Never invokes Persistence.
# - All computation is delegated to sub-pipelines and engines.
# - Never raises; all errors are captured in the result's diagnostics.
# - Deterministic: same inputs produce the same output.

from __future__ import annotations

import time

from domain.contracts.feature.feature_collection import FeatureCollection
from services.coaching_engine.coaching_context import CoachingContext
from services.coaching_engine.coaching_engine import CoachingEngine
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
from services.knowledge_pipeline.knowledge_pipeline import KnowledgePipeline
from services.knowledge_pipeline.knowledge_pipeline_context import KnowledgePipelineContext
from services.narrative_generator.narrative_generation_context import (
    NarrativeGenerationContext,
)
from services.narrative_generator.narrative_generator import NarrativeGenerator
from services.session_close.session_close_pipeline import SessionClosePipeline


class InterviewPipeline:
    """Orchestrates the full interview pipeline across all sub-pipelines.

    Delegation:
    - Knowledge computation:  KnowledgePipeline
    - Narrative generation:   NarrativeGenerator
    - Coaching derivation:    CoachingEngine
    - Session close:          SessionClosePipeline

    This class owns ONLY orchestration: stage sequencing, abort-on-failure
    decisions, metric collection, and result assembly.

    No business logic is implemented here. All domain computation is
    fully delegated to the sub-pipelines and engines.

    Usage::

        pipeline = InterviewPipeline(
            knowledge_pipeline=KnowledgePipeline(...),
            narrative_generator=NarrativeGenerator(),
            coaching_engine=CoachingEngine(),
            session_close_pipeline=SessionClosePipeline(),
        )
        result = pipeline.run(context)
    """

    def __init__(
        self,
        knowledge_pipeline: KnowledgePipeline,
        narrative_generator: NarrativeGenerator,
        coaching_engine: CoachingEngine,
        session_close_pipeline: SessionClosePipeline,
        configuration: InterviewPipelineConfiguration | None = None,
    ) -> None:
        self._knowledge_pipeline = knowledge_pipeline
        self._narrative_generator = narrative_generator
        self._coaching_engine = coaching_engine
        self._session_close_pipeline = session_close_pipeline
        self._configuration = configuration or InterviewPipelineConfiguration()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, context: InterviewPipelineContext) -> InterviewPipelineResult:
        """Execute one full pipeline run for the given context.

        Returns InterviewPipelineResult regardless of success/failure.
        Never raises; errors are captured in the result's diagnostics.
        """
        pipeline_start = time.monotonic()
        stage_records: list[StageAuditRecord] = []

        # Accumulated stage outputs (all start as None)
        profile = None
        features: FeatureCollection = FeatureCollection()
        narrative = None
        coaching_snapshot = None
        session_history = None

        # Metrics accumulators
        kp_ms = 0.0
        ng_ms = 0.0
        ce_ms = 0.0
        sc_ms = 0.0
        features_produced = 0
        sections_built = 0
        insights_built = 0
        coaching_objectives = 0

        # ------------------------------------------------------------------
        # Stage 1: KnowledgePipeline
        # ------------------------------------------------------------------
        t0 = time.monotonic()
        try:
            kp_context = KnowledgePipelineContext(
                session_id=context.session_id,
                candidate_identity_id=context.candidate_identity_id,
                question_index=context.question_index,
                signals=context.signals,
                prior_profile=context.prior_profile,
            )
            kp_result = self._knowledge_pipeline.run(kp_context)
            kp_ms = (time.monotonic() - t0) * 1000.0

            if kp_result.is_successful:
                profile = kp_result.profile
                features = FeatureCollection.from_iterable(kp_result.features)
                features_produced = kp_result.feature_count
                stage_records.append(StageAuditRecord(
                    stage=InterviewPipelineStage.KNOWLEDGE_PIPELINE,
                    completed=True,
                    duration_ms=kp_ms,
                ))
            else:
                stage_records.append(StageAuditRecord(
                    stage=InterviewPipelineStage.KNOWLEDGE_PIPELINE,
                    completed=False,
                    error_message=kp_result.failure_reason,
                    duration_ms=kp_ms,
                ))
                if self._configuration.abort_on_knowledge_pipeline_failure:
                    return self._build_failure_result(
                        context=context,
                        stage_records=stage_records,
                        failure_stage=InterviewPipelineStage.KNOWLEDGE_PIPELINE,
                        failure_reason=kp_result.failure_reason or "KnowledgePipeline failed.",
                        pipeline_start=pipeline_start,
                        kp_ms=kp_ms,
                        ng_ms=ng_ms,
                        ce_ms=ce_ms,
                        sc_ms=sc_ms,
                        signals_received=len(context.signals),
                        features_produced=features_produced,
                        sections_built=sections_built,
                        insights_built=insights_built,
                        coaching_objectives=coaching_objectives,
                        profile=profile,
                        narrative=narrative,
                        coaching_snapshot=coaching_snapshot,
                        session_history=session_history,
                    )
        except Exception as exc:  # noqa: BLE001
            kp_ms = (time.monotonic() - t0) * 1000.0
            stage_records.append(StageAuditRecord(
                stage=InterviewPipelineStage.KNOWLEDGE_PIPELINE,
                completed=False,
                error_message=str(exc),
                duration_ms=kp_ms,
            ))
            if self._configuration.abort_on_knowledge_pipeline_failure:
                return self._build_failure_result(
                    context=context,
                    stage_records=stage_records,
                    failure_stage=InterviewPipelineStage.KNOWLEDGE_PIPELINE,
                    failure_reason=str(exc),
                    pipeline_start=pipeline_start,
                    kp_ms=kp_ms,
                    ng_ms=ng_ms,
                    ce_ms=ce_ms,
                    sc_ms=sc_ms,
                    signals_received=len(context.signals),
                    features_produced=features_produced,
                    sections_built=sections_built,
                    insights_built=insights_built,
                    coaching_objectives=coaching_objectives,
                    profile=profile,
                    narrative=narrative,
                    coaching_snapshot=coaching_snapshot,
                    session_history=session_history,
                )

        # ------------------------------------------------------------------
        # Stage 2: NarrativeGenerator
        # ------------------------------------------------------------------
        t0 = time.monotonic()
        try:
            ng_context = NarrativeGenerationContext(
                session_id=context.session_id,
                candidate_identity_id=context.candidate_identity_id,
                question_index=context.question_index,
                profile=profile or self._empty_profile(),
                features=features,
                knowledge_gap_areas=context.knowledge_gap_observation_ids,
                evaluation_summary=context.evaluation_summary,
                interview_metadata=context.interview_metadata,
            )
            ng_result = self._narrative_generator.generate(ng_context)
            ng_ms = (time.monotonic() - t0) * 1000.0

            if ng_result.is_successful:
                narrative = ng_result.narrative
                sections_built = ng_result.diagnostics.metrics.sections_built
                insights_built = ng_result.diagnostics.metrics.insights_built
                stage_records.append(StageAuditRecord(
                    stage=InterviewPipelineStage.NARRATIVE_GENERATOR,
                    completed=True,
                    duration_ms=ng_ms,
                ))
            else:
                stage_records.append(StageAuditRecord(
                    stage=InterviewPipelineStage.NARRATIVE_GENERATOR,
                    completed=False,
                    error_message=ng_result.failure_reason,
                    duration_ms=ng_ms,
                ))
                if self._configuration.abort_on_narrative_failure:
                    return self._build_failure_result(
                        context=context,
                        stage_records=stage_records,
                        failure_stage=InterviewPipelineStage.NARRATIVE_GENERATOR,
                        failure_reason=ng_result.failure_reason or "NarrativeGenerator failed.",
                        pipeline_start=pipeline_start,
                        kp_ms=kp_ms,
                        ng_ms=ng_ms,
                        ce_ms=ce_ms,
                        sc_ms=sc_ms,
                        signals_received=len(context.signals),
                        features_produced=features_produced,
                        sections_built=sections_built,
                        insights_built=insights_built,
                        coaching_objectives=coaching_objectives,
                        profile=profile,
                        narrative=narrative,
                        coaching_snapshot=coaching_snapshot,
                        session_history=session_history,
                    )
        except Exception as exc:  # noqa: BLE001
            ng_ms = (time.monotonic() - t0) * 1000.0
            stage_records.append(StageAuditRecord(
                stage=InterviewPipelineStage.NARRATIVE_GENERATOR,
                completed=False,
                error_message=str(exc),
                duration_ms=ng_ms,
            ))
            if self._configuration.abort_on_narrative_failure:
                return self._build_failure_result(
                    context=context,
                    stage_records=stage_records,
                    failure_stage=InterviewPipelineStage.NARRATIVE_GENERATOR,
                    failure_reason=str(exc),
                    pipeline_start=pipeline_start,
                    kp_ms=kp_ms,
                    ng_ms=ng_ms,
                    ce_ms=ce_ms,
                    sc_ms=sc_ms,
                    signals_received=len(context.signals),
                    features_produced=features_produced,
                    sections_built=sections_built,
                    insights_built=insights_built,
                    coaching_objectives=coaching_objectives,
                    profile=profile,
                    narrative=narrative,
                    coaching_snapshot=coaching_snapshot,
                    session_history=session_history,
                )

        # ------------------------------------------------------------------
        # Stage 3: CoachingEngine
        # ------------------------------------------------------------------
        t0 = time.monotonic()
        try:
            ce_context = CoachingContext(
                session_id=context.session_id,
                candidate_identity_id=context.candidate_identity_id,
                question_index=context.question_index,
                profile=profile or self._empty_profile(),
                features=features.features,
                knowledge_gap_observation_ids=context.knowledge_gap_observation_ids,
                interview_topic=context.interview_topic,
                interview_role=context.interview_role,
            )
            ce_result = self._coaching_engine.run(ce_context)
            ce_ms = (time.monotonic() - t0) * 1000.0

            if ce_result.is_successful:
                coaching_snapshot = ce_result.snapshot
                coaching_objectives = ce_result.objective_count
                stage_records.append(StageAuditRecord(
                    stage=InterviewPipelineStage.COACHING_ENGINE,
                    completed=True,
                    duration_ms=ce_ms,
                ))
            else:
                stage_records.append(StageAuditRecord(
                    stage=InterviewPipelineStage.COACHING_ENGINE,
                    completed=False,
                    error_message=ce_result.failure_reason,
                    duration_ms=ce_ms,
                ))
                if self._configuration.abort_on_coaching_failure:
                    return self._build_failure_result(
                        context=context,
                        stage_records=stage_records,
                        failure_stage=InterviewPipelineStage.COACHING_ENGINE,
                        failure_reason=ce_result.failure_reason or "CoachingEngine failed.",
                        pipeline_start=pipeline_start,
                        kp_ms=kp_ms,
                        ng_ms=ng_ms,
                        ce_ms=ce_ms,
                        sc_ms=sc_ms,
                        signals_received=len(context.signals),
                        features_produced=features_produced,
                        sections_built=sections_built,
                        insights_built=insights_built,
                        coaching_objectives=coaching_objectives,
                        profile=profile,
                        narrative=narrative,
                        coaching_snapshot=coaching_snapshot,
                        session_history=session_history,
                    )
        except Exception as exc:  # noqa: BLE001
            ce_ms = (time.monotonic() - t0) * 1000.0
            stage_records.append(StageAuditRecord(
                stage=InterviewPipelineStage.COACHING_ENGINE,
                completed=False,
                error_message=str(exc),
                duration_ms=ce_ms,
            ))
            if self._configuration.abort_on_coaching_failure:
                return self._build_failure_result(
                    context=context,
                    stage_records=stage_records,
                    failure_stage=InterviewPipelineStage.COACHING_ENGINE,
                    failure_reason=str(exc),
                    pipeline_start=pipeline_start,
                    kp_ms=kp_ms,
                    ng_ms=ng_ms,
                    ce_ms=ce_ms,
                    sc_ms=sc_ms,
                    signals_received=len(context.signals),
                    features_produced=features_produced,
                    sections_built=sections_built,
                    insights_built=insights_built,
                    coaching_objectives=coaching_objectives,
                    profile=profile,
                    narrative=narrative,
                    coaching_snapshot=coaching_snapshot,
                    session_history=session_history,
                )

        # ------------------------------------------------------------------
        # Stage 4: SessionClosePipeline  (skipped — requires full session context)
        # ------------------------------------------------------------------
        # SessionClosePipeline requires KnowledgeSnapshot and InterviewMetadata,
        # which are richer domain artifacts not available in InterviewPipelineContext.
        # The caller is responsible for assembling those inputs and invoking
        # SessionClosePipeline separately, or providing a pre-built
        # SessionCloseContext. This stage is therefore skipped at this milestone.
        stage_records.append(StageAuditRecord(
            stage=InterviewPipelineStage.SESSION_CLOSE,
            completed=False,
            skipped=True,
            duration_ms=0.0,
        ))

        # ------------------------------------------------------------------
        # Assembly
        # ------------------------------------------------------------------
        total_ms = (time.monotonic() - pipeline_start) * 1000.0
        metrics = InterviewPipelineMetrics(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            knowledge_pipeline_duration_ms=kp_ms,
            narrative_generator_duration_ms=ng_ms,
            coaching_engine_duration_ms=ce_ms,
            session_close_duration_ms=sc_ms,
            total_duration_ms=total_ms,
            signals_received=len(context.signals),
            features_produced=features_produced,
            sections_built=sections_built,
            insights_built=insights_built,
            coaching_objectives_produced=coaching_objectives,
        )
        diagnostics = InterviewPipelineDiagnostics.successful(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            stage_records=tuple(stage_records),
            metrics=metrics,
        )
        return InterviewPipelineResult(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            profile=profile,
            narrative=narrative,
            coaching_snapshot=coaching_snapshot,
            session_history=session_history,
            diagnostics=diagnostics,
            is_successful=True,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _empty_profile(self):  # type: ignore[return]
        """Return a minimal CandidateProfile for downstream stages when KnowledgePipeline
        did not produce a profile (non-aborting failure path)."""
        from domain.contracts.reasoning.candidate_profile import CandidateProfile

        return CandidateProfile(
            questions_answered=0,
            areas_covered=[],
            last_updated_at_question_index=0,
        )

    def _build_failure_result(
        self,
        context: InterviewPipelineContext,
        stage_records: list[StageAuditRecord],
        failure_stage: InterviewPipelineStage,
        failure_reason: str,
        pipeline_start: float,
        kp_ms: float,
        ng_ms: float,
        ce_ms: float,
        sc_ms: float,
        signals_received: int,
        features_produced: int,
        sections_built: int,
        insights_built: int,
        coaching_objectives: int,
        profile,  # type: ignore[assignment]
        narrative,  # type: ignore[assignment]
        coaching_snapshot,  # type: ignore[assignment]
        session_history,  # type: ignore[assignment]
    ) -> InterviewPipelineResult:
        total_ms = (time.monotonic() - pipeline_start) * 1000.0
        metrics = InterviewPipelineMetrics(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            knowledge_pipeline_duration_ms=kp_ms,
            narrative_generator_duration_ms=ng_ms,
            coaching_engine_duration_ms=ce_ms,
            session_close_duration_ms=sc_ms,
            total_duration_ms=total_ms,
            signals_received=signals_received,
            features_produced=features_produced,
            sections_built=sections_built,
            insights_built=insights_built,
            coaching_objectives_produced=coaching_objectives,
        )
        diagnostics = InterviewPipelineDiagnostics.failed(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            stage_records=tuple(stage_records),
            metrics=metrics,
            failure_stage=failure_stage,
            failure_reason=failure_reason,
        )
        return InterviewPipelineResult(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            profile=profile,
            narrative=narrative,
            coaching_snapshot=coaching_snapshot,
            session_history=session_history,
            diagnostics=diagnostics,
            is_successful=False,
            failure_reason=failure_reason,
        )
