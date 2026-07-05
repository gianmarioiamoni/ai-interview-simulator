# services/narrative_generator/narrative_generator.py
# NarrativeGenerator — orchestration layer (E03-M1, ADR-023)
#
# Invariants (ADR-023):
# - Owns orchestration only; NarrativeBuilder is the sole Narrative creator.
# - Never mutates CandidateProfile (N-01).
# - Never computes ProfileFeatures.
# - Never accesses ObservationStore or FeatureEngine internals.
# - No LLM, no PromptLoader, no Prompt templates, no OpenAI calls.
# - Produces deterministic placeholder prose only (real LLM belongs to a later milestone).
# - No persistence, no replay.

from __future__ import annotations

import time

from domain.contracts.feature.feature_collection import FeatureCollection
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.narrative.narrative_builder import NarrativeBuilder
from domain.contracts.narrative.narrative_insight import NarrativeInsight
from domain.contracts.narrative.narrative_insight_type import NarrativeInsightType
from domain.contracts.narrative.narrative_section import NarrativeSection
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType
from services.narrative_generator.narrative_generation_context import NarrativeGenerationContext
from services.narrative_generator.narrative_generation_diagnostics import (
    NarrativeGenerationDiagnostics,
    NarrativeStage,
    StageAuditRecord,
)
from services.narrative_generator.narrative_generation_metrics import NarrativeGenerationMetrics
from services.narrative_generator.narrative_generation_result import NarrativeGenerationResult

# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

# Fallback FeatureIdentity when FeatureCollection is empty (ADR-023 C-01 requires
# at least one feature reference per section; we use a sentinel for placeholder prose).
_SENTINEL_FEATURE_TYPE = FeatureType.TECHNICAL_SKILL
_SENTINEL_IDENTITY: FeatureIdentity = FeatureIdentity.for_type(_SENTINEL_FEATURE_TYPE)

# Deterministic placeholder prose templates (no LLM, no PromptLoader)
_SECTION_PROSE: dict[NarrativeSectionType, str] = {
    NarrativeSectionType.EXECUTIVE_SUMMARY: (
        "Candidate demonstrated engagement across {questions_answered} question(s) "
        "covering {areas_covered}."
    ),
    NarrativeSectionType.STRENGTHS: (
        "Notable strengths were observed in {strength_features}."
    ),
    NarrativeSectionType.WEAKNESSES: (
        "Areas requiring development include {weakness_features}."
    ),
    NarrativeSectionType.GROWTH: (
        "Growth opportunities identified: {growth_areas}."
    ),
    NarrativeSectionType.RECOMMENDATIONS: (
        "Recommended focus areas for future sessions: {recommendations}."
    ),
}

_CONFIDENCE_CONTEXT_TEMPLATE = "Based on {feature_count} feature(s) at session question index {qi}."

# Insight prose templates
_INSIGHT_PROSE: dict[NarrativeInsightType, str] = {
    NarrativeInsightType.STRENGTH_SIGNAL: "Feature '{ftype}' shows a positive signal (value={value}).",
    NarrativeInsightType.RISK_SIGNAL: "Feature '{ftype}' indicates a risk area (value={value}).",
    NarrativeInsightType.GROWTH_OPPORTUNITY: "Feature '{ftype}' presents a growth opportunity.",
    NarrativeInsightType.ANOMALY: "Feature '{ftype}' exhibits an unexpected pattern (value={value}).",
}


class NarrativeGenerator:
    """Orchestrates generation of a Narrative from a NarrativeGenerationContext.

    Owns ONLY orchestration: stage sequencing, section/insight assembly via
    NarrativeBuilder, error capture, metric collection, and result assembly.

    No business logic is implemented here. NarrativeBuilder remains the sole
    permitted Narrative constructor path (ADR-023 §C).

    Deterministic placeholder prose is emitted at this milestone.
    Real prompt integration belongs to a later milestone.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, context: NarrativeGenerationContext) -> NarrativeGenerationResult:
        """Execute one generation cycle for the given context.

        Returns NarrativeGenerationResult regardless of success/failure.
        Never raises; errors are captured in the result's diagnostics.
        """
        cycle_start = time.monotonic()
        stage_records: list[StageAuditRecord] = []

        # --- Stage 1: Context validation ---
        t0 = time.monotonic()
        validation_error, validation_record = self._validate_context(context)
        stage_records.append(validation_record)

        if validation_error is not None:
            return self._abort(
                context=context,
                stage_records=stage_records,
                failure_stage=NarrativeStage.CONTEXT_VALIDATION,
                failure_reason=validation_error,
                cycle_start=cycle_start,
                sections_built=0,
                insights_built=0,
                section_ms=0.0,
                insight_ms=0.0,
            )

        # --- Stage 2: Section build ---
        t1 = time.monotonic()
        sections, section_error, section_record = self._build_sections(context)
        section_ms = (time.monotonic() - t1) * 1000.0
        stage_records.append(section_record)

        if section_error is not None:
            return self._abort(
                context=context,
                stage_records=stage_records,
                failure_stage=NarrativeStage.SECTION_BUILD,
                failure_reason=section_error,
                cycle_start=cycle_start,
                sections_built=0,
                insights_built=0,
                section_ms=section_ms,
                insight_ms=0.0,
            )

        sections_built = len(sections)

        # --- Stage 3: Insight build ---
        t2 = time.monotonic()
        insights, insight_error, insight_record = self._build_insights(context)
        insight_ms = (time.monotonic() - t2) * 1000.0
        stage_records.append(insight_record)

        if insight_error is not None:
            return self._abort(
                context=context,
                stage_records=stage_records,
                failure_stage=NarrativeStage.INSIGHT_BUILD,
                failure_reason=insight_error,
                cycle_start=cycle_start,
                sections_built=sections_built,
                insights_built=0,
                section_ms=section_ms,
                insight_ms=insight_ms,
            )

        insights_built = len(insights)

        # --- Stage 4: Narrative assembly via NarrativeBuilder ---
        t3 = time.monotonic()
        try:
            builder = (
                NarrativeBuilder()
                .with_overview_section(sections[NarrativeSectionType.EXECUTIVE_SUMMARY])
                .with_strengths(sections[NarrativeSectionType.STRENGTHS])
                .with_weaknesses(sections[NarrativeSectionType.WEAKNESSES])
                .with_growth_areas(sections[NarrativeSectionType.GROWTH])
                .with_recommendations(sections[NarrativeSectionType.RECOMMENDATIONS])
                .with_insights(insights)
            )
            narrative = builder.build()
            assembly_record = StageAuditRecord(
                stage=NarrativeStage.NARRATIVE_ASSEMBLY,
                completed=True,
                duration_ms=(time.monotonic() - t3) * 1000.0,
            )
        except Exception as exc:  # noqa: BLE001
            assembly_record = StageAuditRecord(
                stage=NarrativeStage.NARRATIVE_ASSEMBLY,
                completed=False,
                error_message=str(exc),
                duration_ms=(time.monotonic() - t3) * 1000.0,
            )
            stage_records.append(assembly_record)
            return self._abort(
                context=context,
                stage_records=stage_records,
                failure_stage=NarrativeStage.NARRATIVE_ASSEMBLY,
                failure_reason=str(exc),
                cycle_start=cycle_start,
                sections_built=sections_built,
                insights_built=insights_built,
                section_ms=section_ms,
                insight_ms=insight_ms,
            )

        stage_records.append(assembly_record)
        total_ms = (time.monotonic() - cycle_start) * 1000.0

        metrics = NarrativeGenerationMetrics(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            section_build_duration_ms=section_ms,
            insight_build_duration_ms=insight_ms,
            total_duration_ms=total_ms,
            features_received=context.features.size,
            sections_built=sections_built,
            insights_built=insights_built,
        )
        diagnostics = NarrativeGenerationDiagnostics.successful(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            stage_records=tuple(stage_records),
            metrics=metrics,
        )
        return NarrativeGenerationResult(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            narrative=narrative,
            diagnostics=diagnostics,
            is_successful=True,
        )

    # ------------------------------------------------------------------
    # Stage runners
    # ------------------------------------------------------------------

    def _validate_context(
        self, context: NarrativeGenerationContext
    ) -> tuple[str | None, StageAuditRecord]:
        t0 = time.monotonic()
        try:
            if not context.session_id:
                raise ValueError("session_id must be non-empty.")
            if not context.candidate_identity_id:
                raise ValueError("candidate_identity_id must be non-empty.")
            if context.question_index < 0:
                raise ValueError("question_index must be >= 0.")
            duration_ms = (time.monotonic() - t0) * 1000.0
            return None, StageAuditRecord(
                stage=NarrativeStage.CONTEXT_VALIDATION,
                completed=True,
                duration_ms=duration_ms,
            )
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.monotonic() - t0) * 1000.0
            return str(exc), StageAuditRecord(
                stage=NarrativeStage.CONTEXT_VALIDATION,
                completed=False,
                error_message=str(exc),
                duration_ms=duration_ms,
            )

    def _build_sections(
        self, context: NarrativeGenerationContext
    ) -> tuple[dict[NarrativeSectionType, NarrativeSection], str | None, StageAuditRecord]:
        t0 = time.monotonic()
        try:
            sections = self._assemble_sections(context)
            duration_ms = (time.monotonic() - t0) * 1000.0
            return sections, None, StageAuditRecord(
                stage=NarrativeStage.SECTION_BUILD,
                completed=True,
                duration_ms=duration_ms,
            )
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.monotonic() - t0) * 1000.0
            return {}, str(exc), StageAuditRecord(
                stage=NarrativeStage.SECTION_BUILD,
                completed=False,
                error_message=str(exc),
                duration_ms=duration_ms,
            )

    def _build_insights(
        self, context: NarrativeGenerationContext
    ) -> tuple[list[NarrativeInsight], str | None, StageAuditRecord]:
        t0 = time.monotonic()
        try:
            insights = self._assemble_insights(context)
            duration_ms = (time.monotonic() - t0) * 1000.0
            return insights, None, StageAuditRecord(
                stage=NarrativeStage.INSIGHT_BUILD,
                completed=True,
                duration_ms=duration_ms,
            )
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.monotonic() - t0) * 1000.0
            return [], str(exc), StageAuditRecord(
                stage=NarrativeStage.INSIGHT_BUILD,
                completed=False,
                error_message=str(exc),
                duration_ms=duration_ms,
            )

    # ------------------------------------------------------------------
    # Deterministic placeholder assembly
    # ------------------------------------------------------------------

    def _assemble_sections(
        self, context: NarrativeGenerationContext
    ) -> dict[NarrativeSectionType, NarrativeSection]:
        """Build all five mandatory sections from context deterministically.

        Feature references are derived from FeatureCollection in a stable,
        sorted order to guarantee determinism (same input → same output).

        When FeatureCollection is empty, a sentinel FeatureIdentity is used so
        ADR-023 C-01 (non-empty feature_references) is satisfied.
        """
        features = context.features
        feature_count = features.size
        qi = context.question_index

        # Stable sorted feature identities for deterministic references
        sorted_features = list(
            features.sorted_by_type_id().features
        )
        all_ids: tuple[FeatureIdentity, ...] = (
            tuple(f.feature_identity for f in sorted_features)
            if sorted_features
            else (_SENTINEL_IDENTITY,)
        )

        confidence_context = _CONFIDENCE_CONTEXT_TEMPLATE.format(
            feature_count=feature_count, qi=qi
        )
        areas_covered = (
            ", ".join(context.profile.areas_covered)
            if context.profile.areas_covered
            else "general topics"
        )
        questions_answered = context.profile.questions_answered

        # Identify high-confidence vs low-confidence features for strength/weakness slots
        high_confidence = [
            f for f in sorted_features if f.quality.confidence.value >= 0.6
        ]
        low_confidence = [
            f for f in sorted_features if f.quality.confidence.value < 0.4
        ]

        strength_ids: tuple[FeatureIdentity, ...] = (
            tuple(f.feature_identity for f in high_confidence)
            if high_confidence
            else (_SENTINEL_IDENTITY,)
        )
        weakness_ids: tuple[FeatureIdentity, ...] = (
            tuple(f.feature_identity for f in low_confidence)
            if low_confidence
            else (_SENTINEL_IDENTITY,)
        )
        growth_ids = all_ids
        recommendations_ids = all_ids

        strength_labels = ", ".join(
            f.feature_identity.feature_type_id for f in high_confidence
        ) or "technical_skill_feature"
        weakness_labels = ", ".join(
            f.feature_identity.feature_type_id for f in low_confidence
        ) or "none identified"
        gap_labels = ", ".join(context.knowledge_gap_areas) or "none identified"
        rec_labels = ", ".join(
            f"{k}: {v}" for k, v in context.evaluation_summary.items()
        ) or "continue current preparation"

        return {
            NarrativeSectionType.EXECUTIVE_SUMMARY: NarrativeSection(
                section_type=NarrativeSectionType.EXECUTIVE_SUMMARY,
                prose=_SECTION_PROSE[NarrativeSectionType.EXECUTIVE_SUMMARY].format(
                    questions_answered=questions_answered,
                    areas_covered=areas_covered,
                ),
                feature_references=all_ids,
                confidence_context=confidence_context,
            ),
            NarrativeSectionType.STRENGTHS: NarrativeSection(
                section_type=NarrativeSectionType.STRENGTHS,
                prose=_SECTION_PROSE[NarrativeSectionType.STRENGTHS].format(
                    strength_features=strength_labels,
                ),
                feature_references=strength_ids,
                confidence_context=confidence_context,
            ),
            NarrativeSectionType.WEAKNESSES: NarrativeSection(
                section_type=NarrativeSectionType.WEAKNESSES,
                prose=_SECTION_PROSE[NarrativeSectionType.WEAKNESSES].format(
                    weakness_features=weakness_labels,
                ),
                feature_references=weakness_ids,
                confidence_context=confidence_context,
            ),
            NarrativeSectionType.GROWTH: NarrativeSection(
                section_type=NarrativeSectionType.GROWTH,
                prose=_SECTION_PROSE[NarrativeSectionType.GROWTH].format(
                    growth_areas=gap_labels,
                ),
                feature_references=growth_ids,
                confidence_context=confidence_context,
            ),
            NarrativeSectionType.RECOMMENDATIONS: NarrativeSection(
                section_type=NarrativeSectionType.RECOMMENDATIONS,
                prose=_SECTION_PROSE[NarrativeSectionType.RECOMMENDATIONS].format(
                    recommendations=rec_labels,
                ),
                feature_references=recommendations_ids,
                confidence_context=confidence_context,
            ),
        }

    def _assemble_insights(
        self, context: NarrativeGenerationContext
    ) -> list[NarrativeInsight]:
        """Build NarrativeInsights from high-confidence and low-confidence features.

        Deterministic: features processed in stable sorted order (by type_id).
        Each insight traces to exactly one ProfileFeature (ADR-023 C-02).
        """
        insights: list[NarrativeInsight] = []
        sorted_features = list(context.features.sorted_by_type_id().features)

        for feature in sorted_features:
            confidence_value = feature.quality.confidence.value
            ftype = feature.feature_identity.feature_type_id
            value = feature.value

            if confidence_value >= 0.7:
                insight_type = NarrativeInsightType.STRENGTH_SIGNAL
            elif confidence_value < 0.35:
                insight_type = NarrativeInsightType.RISK_SIGNAL
            else:
                insight_type = NarrativeInsightType.GROWTH_OPPORTUNITY

            prose = _INSIGHT_PROSE[insight_type].format(ftype=ftype, value=value)
            insights.append(
                NarrativeInsight(
                    insight_type=insight_type,
                    prose=prose,
                    source_feature_id=feature.feature_identity,
                    confidence=confidence_value,
                )
            )

        return insights

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _abort(
        self,
        context: NarrativeGenerationContext,
        stage_records: list[StageAuditRecord],
        failure_stage: NarrativeStage,
        failure_reason: str,
        cycle_start: float,
        sections_built: int,
        insights_built: int,
        section_ms: float,
        insight_ms: float,
    ) -> NarrativeGenerationResult:
        total_ms = (time.monotonic() - cycle_start) * 1000.0
        metrics = NarrativeGenerationMetrics(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            section_build_duration_ms=section_ms,
            insight_build_duration_ms=insight_ms,
            total_duration_ms=total_ms,
            features_received=context.features.size,
            sections_built=sections_built,
            insights_built=insights_built,
        )
        diagnostics = NarrativeGenerationDiagnostics.failed(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            stage_records=tuple(stage_records),
            metrics=metrics,
            failure_stage=failure_stage,
            failure_reason=failure_reason,
        )
        return NarrativeGenerationResult(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            narrative=None,
            diagnostics=diagnostics,
            is_successful=False,
            failure_reason=failure_reason,
        )
