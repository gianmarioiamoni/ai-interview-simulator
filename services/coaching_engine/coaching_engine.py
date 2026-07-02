# services/coaching_engine/coaching_engine.py
# CoachingEngine — orchestrates CoachingPlan generation from knowledge inputs (ADR-025, E04-M1)
#
# Orchestration stages:
#   ProfileFeatures + KnowledgeGapIDs + CandidateProfile
#   → GapAnalysis → ObjectiveDerivation → ActionDerivation
#   → RecommendationDerivation → PlanAssembly (CoachingBuilder)
#   → CoachingSnapshot (CoachingPlan)
#
# Invariants (ADR-025):
# - Owns orchestration ONLY; no business logic implemented here.
# - CoachingBuilder is the SOLE creator of CoachingSnapshot.
# - CandidateProfile is NEVER mutated.
# - ObservationStore, FeatureEngine, detectors are NEVER accessed.
# - Narrative is NEVER used as a knowledge source.
# - Deterministic: same inputs produce the same output.

from __future__ import annotations

import time
import uuid

from domain.contracts.coaching.coaching_action import ActionCategory, CoachingAction
from domain.contracts.coaching.coaching_builder import CoachingBuilder, CoachingSnapshot
from domain.contracts.coaching.learning_objective import LearningObjective, ObjectivePriority
from domain.contracts.coaching.study_recommendation import ResourceType, StudyRecommendation
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.profile_feature import ProfileFeature
from services.coaching_engine.coaching_context import CoachingContext
from services.coaching_engine.coaching_diagnostics import (
    CoachingDiagnostics,
    CoachingStage,
    CoachingStageRecord,
)
from services.coaching_engine.coaching_metrics import CoachingMetrics
from services.coaching_engine.coaching_result import CoachingResult

# ---------------------------------------------------------------------------
# Feature-type → coaching relevance thresholds
# ---------------------------------------------------------------------------

_WEAK_FEATURE_VALUES: frozenset[str] = frozenset({"LOW", "VERY_LOW", "WEAK", "POOR"})

# Reverse map: feature_type_id string → FeatureType enum
_FEATURE_TYPE_ID_TO_ENUM: dict[str, FeatureType] = {ft.value: ft for ft in FeatureType}
_STRONG_FEATURE_VALUES: frozenset[str] = frozenset({"HIGH", "VERY_HIGH", "STRONG", "EXCELLENT"})

# Map FeatureType → ActionCategory for action derivation
_FEATURE_TYPE_TO_ACTION_CATEGORY: dict[FeatureType, ActionCategory] = {
    FeatureType.TECHNICAL_SKILL: ActionCategory.PRACTICE,
    FeatureType.REASONING: ActionCategory.DEEP_DIVE,
    FeatureType.COMMUNICATION: ActionCategory.REFLECTION,
    FeatureType.LEADERSHIP: ActionCategory.EXPOSURE,
    FeatureType.COLLABORATION: ActionCategory.EXPOSURE,
    FeatureType.ADAPTABILITY: ActionCategory.REFLECTION,
    FeatureType.LEARNING: ActionCategory.REVIEW,
    FeatureType.CONFIDENCE: ActionCategory.REFLECTION,
    FeatureType.LANGUAGE_CAPABILITY: ActionCategory.PRACTICE,
    FeatureType.COVERAGE: ActionCategory.REVIEW,
    FeatureType.TREND: ActionCategory.REVIEW,
}

# Map FeatureType → ResourceType for recommendation derivation
_FEATURE_TYPE_TO_RESOURCE_TYPE: dict[FeatureType, ResourceType] = {
    FeatureType.TECHNICAL_SKILL: ResourceType.EXERCISE,
    FeatureType.REASONING: ResourceType.CONCEPT_REVIEW,
    FeatureType.COMMUNICATION: ResourceType.READING,
    FeatureType.LEADERSHIP: ResourceType.READING,
    FeatureType.COLLABORATION: ResourceType.READING,
    FeatureType.ADAPTABILITY: ResourceType.READING,
    FeatureType.LEARNING: ResourceType.DOCUMENTATION,
    FeatureType.CONFIDENCE: ResourceType.CONCEPT_REVIEW,
    FeatureType.LANGUAGE_CAPABILITY: ResourceType.EXERCISE,
    FeatureType.COVERAGE: ResourceType.DOCUMENTATION,
    FeatureType.TREND: ResourceType.CONCEPT_REVIEW,
}


class CoachingEngine:
    """Orchestrates CoachingPlan generation from current knowledge inputs.

    Accepts ProfileFeatures, KnowledgeGapIDs, CandidateProfile, and interview
    metadata. Produces a CoachingResult containing a CoachingSnapshot via
    CoachingBuilder.

    Delegation:
    - Gap analysis: derived from ProfileFeatures (weak/low feature values) and
      knowledge_gap_observation_ids count.
    - Objective derivation: one LearningObjective per weak/gap feature.
    - Action derivation: one CoachingAction per objective.
    - Recommendation derivation: one StudyRecommendation per objective.
    - Plan assembly: CoachingBuilder.build().

    Never raises; all errors are captured in the result's diagnostics.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, context: CoachingContext) -> CoachingResult:
        """Execute one full CoachingEngine cycle for the given context.

        Returns CoachingResult regardless of success/failure.
        """
        cycle_start = time.monotonic()
        stage_records: list[CoachingStageRecord] = []

        # --- Stage 1: Gap Analysis ---
        t0 = time.monotonic()
        try:
            gap_features, gap_record = self._run_gap_analysis(context)
        except Exception as exc:  # noqa: BLE001
            gap_features, gap_record = [], CoachingStageRecord(
                stage=CoachingStage.GAP_ANALYSIS,
                completed=False,
                error_message=str(exc),
                duration_ms=(time.monotonic() - t0) * 1000.0,
            )
        gap_ms = (time.monotonic() - t0) * 1000.0
        stage_records.append(gap_record)

        if not gap_record.completed:
            return self._build_failure_result(
                context=context,
                stage_records=stage_records,
                failure_stage=CoachingStage.GAP_ANALYSIS,
                failure_reason=gap_record.error_message or "Gap analysis failed.",
                cycle_start=cycle_start,
                gap_ms=gap_ms,
                objective_ms=0.0,
                action_ms=0.0,
                recommendation_ms=0.0,
                assembly_ms=0.0,
                features_consumed=len(context.features),
                gaps_referenced=len(context.knowledge_gap_observation_ids),
                objectives=0,
                actions=0,
                recommendations=0,
            )

        # --- Stage 2: Objective Derivation ---
        t1 = time.monotonic()
        try:
            objectives, objective_record = self._run_objective_derivation(context, gap_features)
        except Exception as exc:  # noqa: BLE001
            objectives, objective_record = [], CoachingStageRecord(
                stage=CoachingStage.OBJECTIVE_DERIVATION,
                completed=False,
                error_message=str(exc),
                duration_ms=(time.monotonic() - t1) * 1000.0,
            )
        objective_ms = (time.monotonic() - t1) * 1000.0
        stage_records.append(objective_record)

        if not objective_record.completed:
            return self._build_failure_result(
                context=context,
                stage_records=stage_records,
                failure_stage=CoachingStage.OBJECTIVE_DERIVATION,
                failure_reason=objective_record.error_message or "Objective derivation failed.",
                cycle_start=cycle_start,
                gap_ms=gap_ms,
                objective_ms=objective_ms,
                action_ms=0.0,
                recommendation_ms=0.0,
                assembly_ms=0.0,
                features_consumed=len(context.features),
                gaps_referenced=len(context.knowledge_gap_observation_ids),
                objectives=0,
                actions=0,
                recommendations=0,
            )

        # --- Stage 3: Action Derivation ---
        t2 = time.monotonic()
        try:
            actions, action_record = self._run_action_derivation(context, objectives)
        except Exception as exc:  # noqa: BLE001
            actions, action_record = [], CoachingStageRecord(
                stage=CoachingStage.ACTION_DERIVATION,
                completed=False,
                error_message=str(exc),
                duration_ms=(time.monotonic() - t2) * 1000.0,
            )
        action_ms = (time.monotonic() - t2) * 1000.0
        stage_records.append(action_record)

        if not action_record.completed:
            return self._build_failure_result(
                context=context,
                stage_records=stage_records,
                failure_stage=CoachingStage.ACTION_DERIVATION,
                failure_reason=action_record.error_message or "Action derivation failed.",
                cycle_start=cycle_start,
                gap_ms=gap_ms,
                objective_ms=objective_ms,
                action_ms=action_ms,
                recommendation_ms=0.0,
                assembly_ms=0.0,
                features_consumed=len(context.features),
                gaps_referenced=len(context.knowledge_gap_observation_ids),
                objectives=len(objectives),
                actions=0,
                recommendations=0,
            )

        # --- Stage 4: Recommendation Derivation ---
        t3 = time.monotonic()
        try:
            recommendations, recommendation_record = self._run_recommendation_derivation(
                context, objectives
            )
        except Exception as exc:  # noqa: BLE001
            recommendations, recommendation_record = [], CoachingStageRecord(
                stage=CoachingStage.RECOMMENDATION_DERIVATION,
                completed=False,
                error_message=str(exc),
                duration_ms=(time.monotonic() - t3) * 1000.0,
            )
        recommendation_ms = (time.monotonic() - t3) * 1000.0
        stage_records.append(recommendation_record)

        if not recommendation_record.completed:
            return self._build_failure_result(
                context=context,
                stage_records=stage_records,
                failure_stage=CoachingStage.RECOMMENDATION_DERIVATION,
                failure_reason=recommendation_record.error_message or "Recommendation derivation failed.",
                cycle_start=cycle_start,
                gap_ms=gap_ms,
                objective_ms=objective_ms,
                action_ms=action_ms,
                recommendation_ms=recommendation_ms,
                assembly_ms=0.0,
                features_consumed=len(context.features),
                gaps_referenced=len(context.knowledge_gap_observation_ids),
                objectives=len(objectives),
                actions=len(actions),
                recommendations=0,
            )

        # --- Stage 5: Plan Assembly (CoachingBuilder) ---
        t4 = time.monotonic()
        try:
            snapshot, assembly_record = self._run_plan_assembly(
                context, objectives, actions, recommendations
            )
        except Exception as exc:  # noqa: BLE001
            snapshot = CoachingBuilder.empty(
                session_id=context.session_id, question_index=context.question_index
            )
            assembly_record = CoachingStageRecord(
                stage=CoachingStage.PLAN_ASSEMBLY,
                completed=False,
                error_message=str(exc),
                duration_ms=(time.monotonic() - t4) * 1000.0,
            )
        assembly_ms = (time.monotonic() - t4) * 1000.0
        stage_records.append(assembly_record)

        if not assembly_record.completed:
            return self._build_failure_result(
                context=context,
                stage_records=stage_records,
                failure_stage=CoachingStage.PLAN_ASSEMBLY,
                failure_reason=assembly_record.error_message or "Plan assembly failed.",
                cycle_start=cycle_start,
                gap_ms=gap_ms,
                objective_ms=objective_ms,
                action_ms=action_ms,
                recommendation_ms=recommendation_ms,
                assembly_ms=assembly_ms,
                features_consumed=len(context.features),
                gaps_referenced=len(context.knowledge_gap_observation_ids),
                objectives=len(objectives),
                actions=len(actions),
                recommendations=len(recommendations),
            )

        total_ms = (time.monotonic() - cycle_start) * 1000.0
        metrics = self._build_metrics(
            context=context,
            gap_ms=gap_ms,
            objective_ms=objective_ms,
            action_ms=action_ms,
            recommendation_ms=recommendation_ms,
            assembly_ms=assembly_ms,
            total_ms=total_ms,
            features_consumed=len(context.features),
            gaps_referenced=len(context.knowledge_gap_observation_ids),
            objectives=len(objectives),
            actions=len(actions),
            recommendations=len(recommendations),
        )
        diagnostics = CoachingDiagnostics.successful(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            stage_records=tuple(stage_records),
            metrics=metrics,
        )
        return CoachingResult(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            snapshot=snapshot,
            diagnostics=diagnostics,
            is_successful=True,
        )

    # ------------------------------------------------------------------
    # Stage runners
    # ------------------------------------------------------------------

    def _run_gap_analysis(
        self, context: CoachingContext
    ) -> tuple[list[ProfileFeature], CoachingStageRecord]:
        """Identify weak/gap features from ProfileFeatures.

        A feature is a gap candidate when its value is in the weak set
        OR when knowledge_gap_observation_ids is non-empty and the feature
        type is TECHNICAL_SKILL, REASONING, or COVERAGE.
        """
        t0 = time.monotonic()
        try:
            gap_features: list[ProfileFeature] = []
            gap_sensitive_type_ids: frozenset[str] = frozenset({
                FeatureType.TECHNICAL_SKILL.value,
                FeatureType.REASONING.value,
                FeatureType.COVERAGE.value,
            })
            for feature in context.features:
                is_weak = feature.value.upper() in _WEAK_FEATURE_VALUES
                is_gap_type = (
                    feature.feature_identity.feature_type_id in gap_sensitive_type_ids
                    and len(context.knowledge_gap_observation_ids) > 0
                )
                if is_weak or is_gap_type:
                    gap_features.append(feature)

            duration_ms = (time.monotonic() - t0) * 1000.0
            return gap_features, CoachingStageRecord(
                stage=CoachingStage.GAP_ANALYSIS,
                completed=True,
                duration_ms=duration_ms,
            )
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.monotonic() - t0) * 1000.0
            return [], CoachingStageRecord(
                stage=CoachingStage.GAP_ANALYSIS,
                completed=False,
                error_message=str(exc),
                duration_ms=duration_ms,
            )

    def _run_objective_derivation(
        self,
        context: CoachingContext,
        gap_features: list[ProfileFeature],
    ) -> tuple[list[LearningObjective], CoachingStageRecord]:
        """Derive one LearningObjective per gap feature."""
        t0 = time.monotonic()
        try:
            objectives: list[LearningObjective] = []
            existing_feature_types: set[FeatureType] = set()

            # Avoid duplicates from prior coaching snapshot
            if context.prior_coaching_snapshot is not None:
                existing_feature_types = {
                    o.feature_type
                    for o in context.prior_coaching_snapshot.objectives
                }

            for feature in gap_features:
                feature_type = _FEATURE_TYPE_ID_TO_ENUM.get(
                    feature.feature_identity.feature_type_id
                )
                if feature_type is None:
                    continue
                if feature_type in existing_feature_types:
                    continue

                priority = self._derive_priority(feature, context)
                confidence = feature.quality.confidence.value

                objective = LearningObjective(
                    objective_id=str(uuid.uuid4()),
                    feature_type=feature_type,
                    description=(
                        f"Improve {feature_type.value.replace('_feature', '').replace('_', ' ')} "
                        f"— current signal: {feature.value}"
                    ),
                    priority=priority,
                    confidence=confidence,
                    supporting_observation_types=(),
                    detected_at_question_index=context.question_index,
                    candidate_identity_id=context.candidate_identity_id,
                )
                objectives.append(objective)
                existing_feature_types.add(feature_type)

            duration_ms = (time.monotonic() - t0) * 1000.0
            return objectives, CoachingStageRecord(
                stage=CoachingStage.OBJECTIVE_DERIVATION,
                completed=True,
                duration_ms=duration_ms,
            )
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.monotonic() - t0) * 1000.0
            return [], CoachingStageRecord(
                stage=CoachingStage.OBJECTIVE_DERIVATION,
                completed=False,
                error_message=str(exc),
                duration_ms=duration_ms,
            )

    def _run_action_derivation(
        self,
        context: CoachingContext,
        objectives: list[LearningObjective],
    ) -> tuple[list[CoachingAction], CoachingStageRecord]:
        """Derive one CoachingAction per LearningObjective."""
        t0 = time.monotonic()
        try:
            actions: list[CoachingAction] = []
            for objective in objectives:
                category = _FEATURE_TYPE_TO_ACTION_CATEGORY.get(
                    objective.feature_type, ActionCategory.REVIEW
                )
                is_immediate = objective.priority in (
                    ObjectivePriority.CRITICAL,
                    ObjectivePriority.HIGH,
                )
                action = CoachingAction(
                    action_id=str(uuid.uuid4()),
                    objective_id=objective.objective_id,
                    category=category,
                    description=(
                        f"{category.value.replace('_', ' ').title()} "
                        f"{objective.feature_type.value.replace('_feature', '').replace('_', ' ')}"
                    ),
                    effort_estimate_hours=self._estimate_effort(objective),
                    is_immediate=is_immediate,
                    tags=frozenset({objective.feature_type.value}),
                )
                actions.append(action)

            duration_ms = (time.monotonic() - t0) * 1000.0
            return actions, CoachingStageRecord(
                stage=CoachingStage.ACTION_DERIVATION,
                completed=True,
                duration_ms=duration_ms,
            )
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.monotonic() - t0) * 1000.0
            return [], CoachingStageRecord(
                stage=CoachingStage.ACTION_DERIVATION,
                completed=False,
                error_message=str(exc),
                duration_ms=duration_ms,
            )

    def _run_recommendation_derivation(
        self,
        context: CoachingContext,
        objectives: list[LearningObjective],
    ) -> tuple[list[StudyRecommendation], CoachingStageRecord]:
        """Derive one StudyRecommendation per LearningObjective.

        Resource Rule (ADR-025): StudyRecommendation references topic labels only.
        No Resource Library is accessed or implemented.
        """
        t0 = time.monotonic()
        try:
            recommendations: list[StudyRecommendation] = []
            for objective in objectives:
                resource_type = _FEATURE_TYPE_TO_RESOURCE_TYPE.get(
                    objective.feature_type, ResourceType.CONCEPT_REVIEW
                )
                topic = (
                    objective.feature_type.value.replace("_feature", "").replace("_", " ").title()
                )
                recommendation = StudyRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    objective_id=objective.objective_id,
                    resource_type=resource_type,
                    topic=topic,
                    rationale=(
                        f"Address identified gap in {topic.lower()} "
                        f"(confidence: {objective.confidence:.2f})"
                    ),
                    estimated_duration_hours=self._estimate_study_duration(objective),
                    tags=frozenset({objective.feature_type.value}),
                )
                recommendations.append(recommendation)

            duration_ms = (time.monotonic() - t0) * 1000.0
            return recommendations, CoachingStageRecord(
                stage=CoachingStage.RECOMMENDATION_DERIVATION,
                completed=True,
                duration_ms=duration_ms,
            )
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.monotonic() - t0) * 1000.0
            return [], CoachingStageRecord(
                stage=CoachingStage.RECOMMENDATION_DERIVATION,
                completed=False,
                error_message=str(exc),
                duration_ms=duration_ms,
            )

    def _run_plan_assembly(
        self,
        context: CoachingContext,
        objectives: list[LearningObjective],
        actions: list[CoachingAction],
        recommendations: list[StudyRecommendation],
    ) -> tuple[CoachingSnapshot, CoachingStageRecord]:
        """Assemble CoachingSnapshot via CoachingBuilder (sole plan creator)."""
        t0 = time.monotonic()
        try:
            snapshot = CoachingBuilder.build(
                objectives=objectives,
                actions=actions,
                recommendations=recommendations,
                session_id=context.session_id,
                question_index=context.question_index,
            )
            duration_ms = (time.monotonic() - t0) * 1000.0
            return snapshot, CoachingStageRecord(
                stage=CoachingStage.PLAN_ASSEMBLY,
                completed=True,
                duration_ms=duration_ms,
            )
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.monotonic() - t0) * 1000.0
            empty_snapshot = CoachingBuilder.empty(
                session_id=context.session_id,
                question_index=context.question_index,
            )
            return empty_snapshot, CoachingStageRecord(
                stage=CoachingStage.PLAN_ASSEMBLY,
                completed=False,
                error_message=str(exc),
                duration_ms=duration_ms,
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _derive_priority(
        feature: ProfileFeature, context: CoachingContext
    ) -> ObjectivePriority:
        """Map feature confidence + value to ObjectivePriority."""
        confidence = feature.quality.confidence.value
        value_upper = feature.value.upper()

        has_knowledge_gaps = len(context.knowledge_gap_observation_ids) > 0

        if value_upper in ("VERY_LOW", "POOR") or (
            has_knowledge_gaps
            and feature.feature_identity.feature_type_id == FeatureType.TECHNICAL_SKILL.value
        ):
            return ObjectivePriority.CRITICAL if confidence >= 0.7 else ObjectivePriority.HIGH

        if value_upper in ("LOW", "WEAK"):
            return ObjectivePriority.HIGH if confidence >= 0.6 else ObjectivePriority.MODERATE

        return ObjectivePriority.MODERATE

    @staticmethod
    def _estimate_effort(objective: LearningObjective) -> float:
        """Estimate effort in hours based on priority."""
        return {
            ObjectivePriority.CRITICAL: 4.0,
            ObjectivePriority.HIGH: 2.0,
            ObjectivePriority.MODERATE: 1.0,
            ObjectivePriority.LOW: 0.5,
        }.get(objective.priority, 1.0)

    @staticmethod
    def _estimate_study_duration(objective: LearningObjective) -> float:
        """Estimate study duration in hours based on priority."""
        return {
            ObjectivePriority.CRITICAL: 3.0,
            ObjectivePriority.HIGH: 2.0,
            ObjectivePriority.MODERATE: 1.0,
            ObjectivePriority.LOW: 0.5,
        }.get(objective.priority, 1.0)

    def _build_metrics(
        self,
        context: CoachingContext,
        gap_ms: float,
        objective_ms: float,
        action_ms: float,
        recommendation_ms: float,
        assembly_ms: float,
        total_ms: float,
        features_consumed: int,
        gaps_referenced: int,
        objectives: int,
        actions: int,
        recommendations: int,
    ) -> CoachingMetrics:
        return CoachingMetrics(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            gap_analysis_duration_ms=gap_ms,
            objective_derivation_duration_ms=objective_ms,
            action_derivation_duration_ms=action_ms,
            recommendation_derivation_duration_ms=recommendation_ms,
            plan_assembly_duration_ms=assembly_ms,
            total_duration_ms=total_ms,
            features_consumed=features_consumed,
            knowledge_gaps_referenced=gaps_referenced,
            objectives_produced=objectives,
            actions_produced=actions,
            recommendations_produced=recommendations,
        )

    def _build_failure_result(
        self,
        context: CoachingContext,
        stage_records: list[CoachingStageRecord],
        failure_stage: CoachingStage,
        failure_reason: str,
        cycle_start: float,
        gap_ms: float,
        objective_ms: float,
        action_ms: float,
        recommendation_ms: float,
        assembly_ms: float,
        features_consumed: int,
        gaps_referenced: int,
        objectives: int,
        actions: int,
        recommendations: int,
    ) -> CoachingResult:
        total_ms = (time.monotonic() - cycle_start) * 1000.0
        metrics = self._build_metrics(
            context=context,
            gap_ms=gap_ms,
            objective_ms=objective_ms,
            action_ms=action_ms,
            recommendation_ms=recommendation_ms,
            assembly_ms=assembly_ms,
            total_ms=total_ms,
            features_consumed=features_consumed,
            gaps_referenced=gaps_referenced,
            objectives=objectives,
            actions=actions,
            recommendations=recommendations,
        )
        diagnostics = CoachingDiagnostics.failed(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            stage_records=tuple(stage_records),
            metrics=metrics,
            failure_stage=failure_stage,
            failure_reason=failure_reason,
        )
        empty_snapshot = CoachingBuilder.empty(
            session_id=context.session_id,
            question_index=context.question_index,
        )
        return CoachingResult(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            question_index=context.question_index,
            snapshot=empty_snapshot,
            diagnostics=diagnostics,
            is_successful=False,
            failure_reason=failure_reason,
        )
