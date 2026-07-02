# services/feature_engine/feature_engine.py
# FeatureEngine — sole producer of ProfileFeature[] (ADR-018 §C, ADR-020 §A–§E)

import time
from collections import defaultdict
from typing import Final

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.feature_composer import FeatureComposer
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_updater import FeatureUpdater
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.observation.observation import Observation
from services.feature_engine.feature_engine_context import FeatureEngineContext
from services.feature_engine.feature_engine_diagnostics import (
    FeatureEngineDiagnostics,
    UpdaterInvocationRecord,
)
from services.feature_engine.feature_engine_metrics import (
    FeatureEngineMetrics,
    UpdaterTimingRecord,
)
from services.feature_engine.feature_engine_result import FeatureEngineResult
from services.feature_engine.feature_resolution_report import (
    CandidateResolutionRecord,
    FeatureResolutionRecord,
    FeatureResolutionReport,
    ResolutionStrategy,
)
from services.feature_engine.feature_update_plan import (
    FeatureUpdatePlan,
    UpdaterInvocationSpec,
)

_ENGINE_VERSION: Final[str] = "1.0.0"


class FeatureEngineError(Exception):
    """Raised when FeatureEngine encounters an unrecoverable orchestration error."""


class FeatureEngine:
    """Knowledge Construction Engine — sole producer of ProfileFeature[] (ADR-020).

    Orchestrates the five-stage pipeline (Pull → Dispatch → Collect → Compose → Commit)
    using a registry of FeatureUpdaters and a FeatureComposer.

    Invariants (ADR-018 §C, ADR-020 §B):
    - NEVER creates Observations.
    - NEVER performs extraction or evaluation.
    - NEVER invokes LLM calls.
    - NEVER writes to ObservationStore.
    - NEVER creates Narrative or CoachingActions.
    - Sole writer to CandidateProfile.features (Domain Invariant I-02).

    The engine is stateless between calls; all per-cycle state is local to run().
    """

    def __init__(
        self,
        updaters: list[FeatureUpdater],
        composer: FeatureComposer,
        engine_version: str = _ENGINE_VERSION,
    ) -> None:
        if not updaters:
            raise FeatureEngineError("FeatureEngine requires at least one FeatureUpdater")
        # Sort once at construction; invocation_order is deterministic (ADR-020 §D)
        self._updaters: tuple[FeatureUpdater, ...] = tuple(
            sorted(updaters, key=lambda u: u.invocation_order)
        )
        self._composer = composer
        self._engine_version = engine_version
        self._validate_updater_registry()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, context: FeatureEngineContext) -> FeatureEngineResult:
        """Execute one full computation cycle.

        ADR-020 §C pipeline:
        1. Pull   — receive snapshot from context (already done by caller)
        2. Dispatch — invoke updaters in invocation_order
        3. Collect  — gather all FeatureCandidates
        4. Compose  — resolve via FeatureComposer
        5. Commit   — return result (caller commits to CandidateProfile)
        """
        cycle_start = time.monotonic()

        plan = self._build_plan(context)
        observations = list(context.snapshot.observations)

        updater_records: list[UpdaterInvocationRecord] = []
        updater_timings: list[UpdaterTimingRecord] = []
        all_candidates: list[FeatureCandidate] = []

        # Step 2+3: Dispatch & Collect
        for spec in plan.updater_specs:
            updater = self._find_updater(spec.updater_id)
            if updater is None:
                continue
            obs_subset = self._filter_observations(observations, updater, spec)
            t0 = time.monotonic()
            candidates = updater.produce(obs_subset)
            duration_ms = (time.monotonic() - t0) * 1000.0

            all_candidates.extend(candidates)
            updater_records.append(
                UpdaterInvocationRecord(
                    updater_id=spec.updater_id,
                    invocation_order=spec.invocation_order,
                    observation_ids_received=tuple(str(o.id) for o in obs_subset),
                    candidate_feature_type_ids_produced=tuple(
                        c.feature_identity.feature_type_id for c in candidates
                    ),
                    duration_ms=duration_ms,
                )
            )
            updater_timings.append(
                UpdaterTimingRecord(
                    updater_id=spec.updater_id,
                    duration_ms=duration_ms,
                    candidates_produced=len(candidates),
                )
            )

        # Step 4: Compose
        t_compose = time.monotonic()
        features, resolution_report = self._compose(
            all_candidates, context, plan
        )
        compose_ms = (time.monotonic() - t_compose) * 1000.0

        # Step 5: Result (commit is caller's responsibility)
        t_commit = time.monotonic()
        commit_ms = (time.monotonic() - t_commit) * 1000.0
        total_ms = (time.monotonic() - cycle_start) * 1000.0

        metrics = FeatureEngineMetrics(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            current_question_index=context.current_question_index,
            total_cycle_duration_ms=total_ms,
            updater_timings=tuple(updater_timings),
            composer_duration_ms=compose_ms,
            commit_duration_ms=commit_ms,
            features_computed=len(features),
            candidates_collected=len(all_candidates),
            observation_count=len(observations),
            is_incremental=plan.is_incremental,
            is_replay=plan.is_replay,
        )
        diagnostics = FeatureEngineDiagnostics(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            current_question_index=context.current_question_index,
            plan=plan,
            updater_invocation_records=tuple(updater_records),
            resolution_report=resolution_report,
            metrics=metrics,
            is_replay=context.is_replay,
        )
        return FeatureEngineResult(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            current_question_index=context.current_question_index,
            features=tuple(features),
            diagnostics=diagnostics,
            is_successful=True,
        )

    @property
    def registered_updater_ids(self) -> tuple[str, ...]:
        return tuple(u.updater_id for u in self._updaters)

    @property
    def engine_version(self) -> str:
        return self._engine_version

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_updater_registry(self) -> None:
        seen_ids: set[str] = set()
        for updater in self._updaters:
            if updater.updater_id in seen_ids:
                raise FeatureEngineError(
                    f"Duplicate updater_id '{updater.updater_id}' in registry"
                )
            seen_ids.add(updater.updater_id)

    def _build_plan(self, context: FeatureEngineContext) -> FeatureUpdatePlan:
        specs = tuple(
            UpdaterInvocationSpec(
                updater_id=u.updater_id,
                invocation_order=u.invocation_order,
                is_incremental=False,
            )
            for u in self._updaters
            if not context.is_replay or u.updater_id == "replay_updater"
        )
        return FeatureUpdatePlan(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            current_question_index=context.current_question_index,
            updater_specs=specs,
            is_full_recomputation=True,
            is_incremental=False,
            is_replay=context.is_replay,
        )

    def _find_updater(self, updater_id: str) -> FeatureUpdater | None:
        for u in self._updaters:
            if u.updater_id == updater_id:
                return u
        return None

    def _filter_observations(
        self,
        observations: list[Observation],
        updater: FeatureUpdater,
        spec: UpdaterInvocationSpec,
    ) -> list[Observation]:
        """Filter observations to those relevant for this Updater.

        Updaters receive only observations whose type is in their observation_type_set.
        If observation_type_set is empty, all observations are passed (wildcard).
        ADR-020 §D: single-pass principle — observations are not re-queried.
        """
        if not updater.observation_type_set:
            return observations
        return [
            o for o in observations
            if o.observation_type.value in updater.observation_type_set
        ]

    def _compose(
        self,
        candidates: list[FeatureCandidate],
        context: FeatureEngineContext,
        plan: FeatureUpdatePlan,
    ) -> tuple[list[ProfileFeature], FeatureResolutionReport]:
        """Step 4: Compose — invoke FeatureComposer and build resolution report."""
        features = self._composer.compose(
            candidates,
            context.candidate_identity_id,
            context.feature_engine_version,
        )

        # Build resolution report from composition results
        # Group candidates by feature_type_id for report construction
        by_type: dict[str, list[FeatureCandidate]] = defaultdict(list)
        for c in candidates:
            by_type[c.feature_identity.feature_type_id].append(c)

        feature_by_type = {f.feature_identity.feature_type_id: f for f in features}
        resolution_records = []

        for type_id, type_candidates in by_type.items():
            pf = feature_by_type.get(type_id)
            if pf is None:
                continue
            strategy = (
                ResolutionStrategy.SINGLE_CANDIDATE
                if len(type_candidates) == 1
                else ResolutionStrategy.MERGED
            )
            candidate_records = tuple(
                CandidateResolutionRecord(
                    updater_id=c.updater_id,
                    candidate_value=c.candidate_value,
                    candidate_confidence=c.candidate_confidence,
                    source_observation_count=len(c.source_observation_ids),
                    was_winner=(c.candidate_value == pf.value),
                    was_superseded=False,
                )
                for c in type_candidates
            )
            resolution_records.append(
                FeatureResolutionRecord(
                    feature_type_id=type_id,
                    strategy=strategy,
                    final_value=pf.value,
                    final_confidence=pf.quality.confidence.value,
                    candidate_records=candidate_records,
                )
            )

        merge_count = sum(1 for r in resolution_records if r.strategy == ResolutionStrategy.MERGED)
        replace_count = sum(1 for r in resolution_records if r.strategy == ResolutionStrategy.REPLACED)
        single_count = sum(1 for r in resolution_records if r.strategy == ResolutionStrategy.SINGLE_CANDIDATE)

        report = FeatureResolutionReport(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            current_question_index=context.current_question_index,
            total_candidates_received=len(candidates),
            total_features_resolved=len(features),
            merge_resolutions=merge_count,
            replace_resolutions=replace_count,
            single_candidate_resolutions=single_count,
            resolution_records=tuple(resolution_records),
        )
        return features, report
