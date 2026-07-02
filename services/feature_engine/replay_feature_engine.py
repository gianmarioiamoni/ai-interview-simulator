# services/feature_engine/replay_feature_engine.py
# ReplayFeatureEngine — replay path engine (ADR-020 §H, §D)

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


class ReplayFeatureEngine(FeatureEngine):
    """Replay path engine — reconstructs ProfileFeatures from a SessionHistory snapshot.

    ADR-020 §H (Replay Recomputation), §D (Replay path invocation order):
    - Invokes only Updaters with updater_id == 'replay_updater'.
    - Never runs live path Updaters (ObservationUpdater, CalibrationUpdater).
    - context.is_replay must be True.
    - In V1.2, replay uses stored CandidateProfileSnapshot. This engine provides
      the interface for V1.3+ per-question-index profile reconstruction.

    Produces a reconstruction_delta_summary comparing the new features against
    any stored_features passed in.
    """

    def __init__(
        self,
        updaters: list[FeatureUpdater],
        composer: FeatureComposer,
        engine_version: str = "1.0.0",
    ) -> None:
        # ReplayFeatureEngine requires at least one replay-path updater
        replay_updaters = [u for u in updaters if u.updater_id == "replay_updater"]
        if not replay_updaters:
            raise FeatureEngineError(
                "ReplayFeatureEngine requires a FeatureUpdater with updater_id='replay_updater'"
            )
        super().__init__(updaters, composer, engine_version)

    def run(self, context: FeatureEngineContext) -> FeatureEngineResult:
        if not context.is_replay:
            raise FeatureEngineError(
                "ReplayFeatureEngine.run() requires context.is_replay=True"
            )
        return super().run(context)

    def run_with_comparison(
        self,
        context: FeatureEngineContext,
        stored_features: tuple[ProfileFeature, ...],
    ) -> FeatureEngineResult:
        """Run replay and compare reconstructed features against stored snapshot.

        ADR-020 §K (Replay Diagnostics): produces a delta summary comparing
        reconstructed ProfileFeature values against stored CandidateProfileSnapshot.
        """
        if not context.is_replay:
            raise FeatureEngineError(
                "ReplayFeatureEngine.run_with_comparison() requires context.is_replay=True"
            )
        result = self.run(context)
        delta_summary = self._compute_delta(result.features, stored_features)

        # Rebuild diagnostics with delta summary
        prior_diag = result.diagnostics
        from services.feature_engine.feature_engine_diagnostics import FeatureEngineDiagnostics
        updated_diagnostics = FeatureEngineDiagnostics(
            session_id=prior_diag.session_id,
            candidate_identity_id=prior_diag.candidate_identity_id,
            current_question_index=prior_diag.current_question_index,
            plan=prior_diag.plan,
            updater_invocation_records=prior_diag.updater_invocation_records,
            resolution_report=prior_diag.resolution_report,
            metrics=prior_diag.metrics,
            is_replay=True,
            reconstruction_delta_summary=delta_summary,
        )
        from pydantic import BaseModel
        return FeatureEngineResult(
            session_id=result.session_id,
            candidate_identity_id=result.candidate_identity_id,
            current_question_index=result.current_question_index,
            features=result.features,
            diagnostics=updated_diagnostics,
            is_successful=result.is_successful,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_delta(
        self,
        reconstructed: tuple[ProfileFeature, ...],
        stored: tuple[ProfileFeature, ...],
    ) -> str:
        """Compute a human-readable delta between reconstructed and stored features."""
        stored_by_type = {f.feature_identity.feature_type_id: f for f in stored}
        reconstructed_by_type = {f.feature_identity.feature_type_id: f for f in reconstructed}

        deltas: list[str] = []
        all_types = set(stored_by_type) | set(reconstructed_by_type)

        for type_id in sorted(all_types):
            s = stored_by_type.get(type_id)
            r = reconstructed_by_type.get(type_id)
            if s is None:
                deltas.append(f"+{type_id}:{r.value if r else '?'} (new in reconstruction)")
            elif r is None:
                deltas.append(f"-{type_id}:{s.value} (missing in reconstruction)")
            elif s.value != r.value:
                deltas.append(f"~{type_id}:{s.value}->{r.value}")

        if not deltas:
            return "no_delta: reconstructed features match stored snapshot"
        return "; ".join(deltas)
