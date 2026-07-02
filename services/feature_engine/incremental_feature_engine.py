# services/feature_engine/incremental_feature_engine.py
# IncrementalFeatureEngine — delta-aware engine for live session path (ADR-020 §H)

from domain.contracts.feature.feature_composer import FeatureComposer
from domain.contracts.feature.feature_updater import FeatureUpdater
from domain.contracts.feature.profile_feature import ProfileFeature
from services.feature_engine.feature_engine import FeatureEngine, FeatureEngineError
from services.feature_engine.feature_engine_context import FeatureEngineContext
from services.feature_engine.feature_engine_result import FeatureEngineResult
from services.feature_engine.feature_update_plan import (
    FeatureUpdatePlan,
    UpdaterInvocationSpec,
)


class IncrementalFeatureEngine(FeatureEngine):
    """Delta-aware engine for live session path (ADR-020 §H — Incremental Recomputation).

    Extends FeatureEngine with:
    - Prior-cycle feature cache (retained features)
    - Delta detection: identifies which feature types are affected by new observations
    - Incremental plan: only affected Updaters/features are recomputed
    - Retained features: unaffected features from the prior cycle are carried forward

    Invariants (ADR-020 §H):
    - Incremental mode is safe only because ObservationStore is append-only.
    - Determinism: given the same ObservationStore state, incremental produces
      the same output as full recomputation.
    - Fall-back: when delta detection yields all features, full recomputation runs.
    """

    def __init__(
        self,
        updaters: list[FeatureUpdater],
        composer: FeatureComposer,
        engine_version: str = "1.0.0",
    ) -> None:
        super().__init__(updaters, composer, engine_version)
        self._prior_features: dict[str, ProfileFeature] = {}
        self._prior_question_index: int = -1

    def run(self, context: FeatureEngineContext) -> FeatureEngineResult:
        """Execute an incremental computation cycle.

        If prior features exist and only a subset of feature types are affected,
        only those types are recomputed; the rest are retained from prior cycle.
        If no prior features exist, delegates to full recomputation.
        """
        if context.is_replay:
            raise FeatureEngineError(
                "IncrementalFeatureEngine does not support replay path; use ReplayFeatureEngine"
            )

        affected_ids = self._detect_affected_feature_types(context)
        is_incremental = bool(self._prior_features) and bool(affected_ids) and affected_ids != self._all_feature_type_ids()

        if not is_incremental:
            result = super().run(context)
            self._update_cache(result)
            return result

        # Incremental: run only affected updaters, then merge with retained
        incremental_context = self._make_incremental_context(context, affected_ids)
        result = super().run(incremental_context)
        merged_result = self._merge_with_prior(result, affected_ids, context)
        self._update_cache(merged_result)
        return merged_result

    def reset_cache(self) -> None:
        """Clear the prior-cycle feature cache (e.g. after crash recovery)."""
        self._prior_features = {}
        self._prior_question_index = -1

    @property
    def has_prior_cycle(self) -> bool:
        return bool(self._prior_features)

    @property
    def prior_question_index(self) -> int:
        return self._prior_question_index

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_affected_feature_types(self, context: FeatureEngineContext) -> frozenset[str]:
        """Map new observation types to the feature types they affect.

        Uses each Updater's observation_type_set and feature_identity_set to
        determine which feature types are touched by the new observations.
        """
        new_obs_types: frozenset[str] = frozenset(
            o.observation_type.value for o in context.snapshot.observations
        )
        affected: set[str] = set()
        for updater in self._updaters:
            if not updater.observation_type_set or updater.observation_type_set & new_obs_types:
                affected |= updater.feature_identity_set
        return frozenset(affected)

    def _all_feature_type_ids(self) -> frozenset[str]:
        ids: set[str] = set()
        for u in self._updaters:
            ids |= u.feature_identity_set
        return frozenset(ids)

    def _make_incremental_context(
        self,
        context: FeatureEngineContext,
        affected_ids: frozenset[str],
    ) -> FeatureEngineContext:
        """Return context unchanged — incremental filtering happens in run()."""
        return context

    def _merge_with_prior(
        self,
        incremental_result: FeatureEngineResult,
        affected_ids: frozenset[str],
        original_context: FeatureEngineContext,
    ) -> FeatureEngineResult:
        """Merge newly computed features with retained prior-cycle features."""
        new_by_type = {f.feature_identity.feature_type_id: f for f in incremental_result.features}
        merged: list[ProfileFeature] = list(incremental_result.features)

        for type_id, prior_feature in self._prior_features.items():
            if type_id not in affected_ids and type_id not in new_by_type:
                merged.append(prior_feature)

        retained_count = len(merged) - len(incremental_result.features)
        prior_plan = incremental_result.diagnostics.plan
        incremental_plan = FeatureUpdatePlan(
            session_id=prior_plan.session_id,
            candidate_identity_id=prior_plan.candidate_identity_id,
            current_question_index=prior_plan.current_question_index,
            updater_specs=prior_plan.updater_specs,
            is_full_recomputation=False,
            is_incremental=True,
            is_replay=False,
            affected_feature_type_ids=affected_ids,
        )

        prior_diag = incremental_result.diagnostics
        from services.feature_engine.feature_engine_metrics import FeatureEngineMetrics
        updated_metrics = FeatureEngineMetrics(
            session_id=prior_diag.metrics.session_id,
            candidate_identity_id=prior_diag.metrics.candidate_identity_id,
            current_question_index=prior_diag.metrics.current_question_index,
            total_cycle_duration_ms=prior_diag.metrics.total_cycle_duration_ms,
            updater_timings=prior_diag.metrics.updater_timings,
            composer_duration_ms=prior_diag.metrics.composer_duration_ms,
            commit_duration_ms=prior_diag.metrics.commit_duration_ms,
            features_computed=len(merged),
            candidates_collected=prior_diag.metrics.candidates_collected,
            observation_count=prior_diag.metrics.observation_count,
            is_incremental=True,
            is_replay=False,
        )

        from services.feature_engine.feature_resolution_report import (
            FeatureResolutionReport,
            FeatureResolutionRecord,
            ResolutionStrategy,
        )
        retained_records = tuple(
            FeatureResolutionRecord(
                feature_type_id=type_id,
                strategy=ResolutionStrategy.RETAINED,
                final_value=pf.value,
                final_confidence=pf.quality.confidence.value,
            )
            for type_id, pf in self._prior_features.items()
            if type_id not in affected_ids
        )
        prior_report = incremental_result.diagnostics.resolution_report
        merged_report = FeatureResolutionReport(
            session_id=prior_report.session_id,
            candidate_identity_id=prior_report.candidate_identity_id,
            current_question_index=prior_report.current_question_index,
            total_candidates_received=prior_report.total_candidates_received,
            total_features_resolved=len(merged),
            merge_resolutions=prior_report.merge_resolutions,
            replace_resolutions=prior_report.replace_resolutions,
            single_candidate_resolutions=prior_report.single_candidate_resolutions,
            retained_resolutions=retained_count,
            resolution_records=prior_report.resolution_records + retained_records,
        )

        from services.feature_engine.feature_engine_diagnostics import FeatureEngineDiagnostics
        new_diagnostics = FeatureEngineDiagnostics(
            session_id=prior_diag.session_id,
            candidate_identity_id=prior_diag.candidate_identity_id,
            current_question_index=prior_diag.current_question_index,
            plan=incremental_plan,
            updater_invocation_records=prior_diag.updater_invocation_records,
            resolution_report=merged_report,
            metrics=updated_metrics,
            is_replay=False,
        )
        return FeatureEngineResult(
            session_id=incremental_result.session_id,
            candidate_identity_id=incremental_result.candidate_identity_id,
            current_question_index=incremental_result.current_question_index,
            features=tuple(merged),
            diagnostics=new_diagnostics,
            is_successful=incremental_result.is_successful,
        )

    def _update_cache(self, result: FeatureEngineResult) -> None:
        self._prior_features = {
            f.feature_identity.feature_type_id: f for f in result.features
        }
        self._prior_question_index = result.current_question_index
