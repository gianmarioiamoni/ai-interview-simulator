# domain/contracts/replay/replay_session.py
# ADR-026 §B6 — ReplaySession (runtime orchestrator for replay operations)

from __future__ import annotations

from datetime import datetime, timezone


class ReplayError(Exception):
    """Raised when a replay operation cannot be completed (ADR-026 §B6).

    Signals unrecoverable failure: KnowledgeSnapshot unavailable or corrupted,
    or invariant violation detected during assembly.
    """


from domain.contracts.knowledge_snapshot.knowledge_snapshot import KnowledgeSnapshot
from domain.contracts.replay.replay_context import ReplayContext
from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode, ReplaySourcePriority
from domain.contracts.replay.replay_manifest import ReplayManifest
from domain.contracts.replay.replay_result import ReplayResult
from domain.contracts.replay.replay_validator import ReplayValidator


class ReplaySession:
    """Assembles a ReplayResult from a ReplayContext without invoking any live pipeline.

    ADR-026 §B6 canonical runtime flow:
        SessionHistory (external) → ReplayContext → ReplaySession.run() → ReplayResult

    Contract:
    - Never invokes FeatureEngine (SP-02, ADR-026 rules).
    - Never invokes NarrativeGenerator.
    - Never invokes CoachingEngine.
    - All output values are exact object references from KnowledgeSnapshot (RC-03).
    - Produces ReplayManifest recording source used per component (SP-03).
    - Read-only: never writes to SessionHistory, ObservationStore, or any pipeline.

    This is the single authoritative entry point for all replay operations.
    """

    def __init__(self, validate_on_run: bool = True) -> None:
        """
        Args:
            validate_on_run: When True, ReplayValidator.validate_result() is called
                             before returning. Defaults to True.
        """
        self._validate_on_run = validate_on_run

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, context: ReplayContext) -> ReplayResult:
        """Execute a replay operation and return the assembled ReplayResult.

        Args:
            context: Validated ReplayContext carrying KnowledgeSnapshot.

        Returns:
            ReplayResult with all components read from KnowledgeSnapshot.

        Raises:
            ReplayError: When context is invalid or assembly invariants are violated.
        """
        context_validation = ReplayValidator.validate_context(context)
        if not context_validation.is_valid:
            raise ReplayError(
                f"ReplayContext validation failed: {list(context_validation.violations)}"
            )

        snapshot = context.knowledge_snapshot
        source_map = self._resolve_sources(snapshot, context.replay_level)
        schema_notes = self._collect_schema_version_notes(snapshot)

        manifest = self._build_manifest(context, source_map, schema_notes)

        result = ReplayResult(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            replay_mode=context.replay_mode,
            replay_level=context.replay_level,
            profile_snapshot=snapshot.profile_snapshot,
            narrative=snapshot.narrative,
            coaching_snapshot=snapshot.coaching_snapshot,
            policy_versions=snapshot.policy_versions,
            knowledge_epoch=snapshot.knowledge_epoch,
            manifest=manifest,
            is_successful=True,
            failure_reason=None,
        )

        if self._validate_on_run:
            result_validation = ReplayValidator.validate_result(result, context)
            if not result_validation.is_valid:
                raise ReplayError(
                    f"ReplayResult invariant violation: {list(result_validation.violations)}"
                )

        return result

    # ------------------------------------------------------------------
    # Internal helpers — no live pipeline invocation
    # ------------------------------------------------------------------

    def _resolve_sources(
        self,
        snapshot: KnowledgeSnapshot,
        replay_level: ReplayLevel,
    ) -> dict[str, ReplaySourcePriority]:
        """Determine source priority for each component (SP-01 through SP-04).

        In standard replay all components come from Priority 1 (KnowledgeSnapshot).
        The hierarchy descent for partial availability is noted here for future use;
        in V1.2 all paths must reach Priority 1.
        """
        # SP-01: KnowledgeSnapshot is always the first source queried.
        # In V1.2 standard replay, Priority 1 is always used — snapshot is always present
        # by contract (ReplayContext requires a KnowledgeSnapshot).
        base_priority = ReplaySourcePriority.KNOWLEDGE_SNAPSHOT

        source_map: dict[str, ReplaySourcePriority] = {
            "profile": base_priority,
            "narrative": base_priority,
            "coaching": base_priority,
            "policy_versions": base_priority,
        }

        # Level 2 also surfaces observation store (still read from snapshot, Priority 1)
        if replay_level == ReplayLevel.KNOWLEDGE:
            source_map["observation_store_snapshot"] = base_priority

        return source_map

    def _collect_schema_version_notes(self, snapshot: KnowledgeSnapshot) -> list[str]:
        """Collect non-modifying schema version mismatch notes (RC-02).

        Notes are informational only — they never alter stored values.
        """
        notes: list[str] = []
        pv = snapshot.policy_versions
        current_epoch = "1"  # V1.2 epoch constant

        if snapshot.knowledge_epoch != current_epoch:
            notes.append(
                f"RC-02: knowledge_epoch='{snapshot.knowledge_epoch}' differs from "
                f"current platform epoch='{current_epoch}'. "
                "Displaying stored values without modification."
            )

        return notes

    def _build_manifest(
        self,
        context: ReplayContext,
        source_per_component: dict[str, ReplaySourcePriority],
        schema_version_notes: list[str],
    ) -> ReplayManifest:
        """Build the ReplayManifest for this operation (SP-03, ADR-026 §D)."""
        migration_metadata = None

        if context.replay_mode in (ReplayMode.MIGRATION, ReplayMode.RECOVERY):
            from domain.contracts.replay.replay_manifest import MigrationMetadata
            migration_metadata = MigrationMetadata(
                trigger_reason="Operator-triggered replay",
                operator_id=context.operator_id or "",
                feature_engine_version_used=(
                    context.knowledge_snapshot.policy_versions.feature_engine_version
                ),
                reconstruction_timestamp=datetime.now(tz=timezone.utc),
                is_reconstructed=True,
            )

        return ReplayManifest(
            session_id=context.session_id,
            candidate_identity_id=context.candidate_identity_id,
            replay_mode=context.replay_mode,
            replay_level=context.replay_level,
            replay_timestamp=datetime.now(tz=timezone.utc),
            replay_engine_version=context.replay_engine_version,
            source_per_component=source_per_component,
            migration_metadata=migration_metadata,
            schema_version_notes=schema_version_notes,
        )
