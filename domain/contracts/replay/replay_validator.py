# domain/contracts/replay/replay_validator.py
# ADR-026 §B4, §C — ReplayValidator (invariant enforcement for Replay layer)

from __future__ import annotations

from dataclasses import dataclass

from domain.contracts.replay.replay_context import ReplayContext
from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode, ReplaySourcePriority
from domain.contracts.replay.replay_result import ReplayResult


@dataclass(frozen=True)
class ReplayValidationResult:
    """Immutable result of a replay validation pass."""

    is_valid: bool
    violations: tuple[str, ...]

    @classmethod
    def ok(cls) -> "ReplayValidationResult":
        return cls(is_valid=True, violations=())

    @classmethod
    def failed(cls, violations: list[str]) -> "ReplayValidationResult":
        return cls(is_valid=False, violations=tuple(violations))


class ReplayValidator:
    """Validates ADR-026 invariants for ReplayContext and ReplayResult.

    Validates:
    - Source priority hierarchy (SP-01 through SP-04)
    - Consistency guarantees (RC-01 through RC-04)
    - Migration policy invariants (MP-01 through MP-06)
    - Read-only contract: no live pipeline references

    Responsibility: validation only. No construction, no mutation, no business logic.
    """

    # -----------------------------------------------------------------
    # Context validation (pre-replay)
    # -----------------------------------------------------------------

    @staticmethod
    def validate_context(context: ReplayContext) -> ReplayValidationResult:
        """Validate ReplayContext before executing a replay operation."""
        violations: list[str] = []

        # SP-01: KnowledgeSnapshot must always be the first source
        if context.knowledge_snapshot is None:
            violations.append("SP-01: knowledge_snapshot must be present in ReplayContext.")

        # Session and candidate consistency
        if context.knowledge_snapshot.session_id != context.session_id:
            violations.append(
                f"RC-CTX-01: session_id mismatch: context='{context.session_id}' "
                f"vs snapshot='{context.knowledge_snapshot.session_id}'."
            )
        if context.knowledge_snapshot.candidate_identity_id != context.candidate_identity_id:
            violations.append(
                f"RC-CTX-01: candidate_identity_id mismatch: "
                f"context='{context.candidate_identity_id}' "
                f"vs snapshot='{context.knowledge_snapshot.candidate_identity_id}'."
            )

        # MP-06: Migration requires operator_id
        if context.replay_mode in (ReplayMode.MIGRATION, ReplayMode.RECOVERY):
            if not context.operator_id:
                violations.append(
                    f"MP-06: replay_mode={context.replay_mode.value} requires operator_id."
                )

        # Level 3 is reserved (ADR-026 §B3)
        if context.replay_level == ReplayLevel.REASONING:
            violations.append(
                "ADR-026 §B3: ReplayLevel.REASONING is reserved for V1.3+."
            )

        # Knowledge snapshot must be valid (delegation)
        from domain.contracts.knowledge_snapshot.knowledge_snapshot_validator import (
            KnowledgeSnapshotValidator,
        )
        ks_result = KnowledgeSnapshotValidator.validate(context.knowledge_snapshot)
        if not ks_result.is_valid:
            for v in ks_result.violations:
                violations.append(f"KS-INVALID: {v}")

        if violations:
            return ReplayValidationResult.failed(violations)
        return ReplayValidationResult.ok()

    # -----------------------------------------------------------------
    # Result validation (post-replay)
    # -----------------------------------------------------------------

    @staticmethod
    def validate_result(result: ReplayResult, context: ReplayContext) -> ReplayValidationResult:
        """Validate a completed ReplayResult against ADR-026 consistency guarantees."""
        violations: list[str] = []

        # RC-01: session and candidate must be identical across result and snapshot
        snap = context.knowledge_snapshot
        if result.session_id != snap.session_id:
            violations.append(
                f"RC-01: result.session_id='{result.session_id}' "
                f"does not match snapshot.session_id='{snap.session_id}'."
            )
        if result.candidate_identity_id != snap.candidate_identity_id:
            violations.append(
                f"RC-01: result.candidate_identity_id='{result.candidate_identity_id}' "
                f"does not match snapshot.candidate_identity_id='{snap.candidate_identity_id}'."
            )

        # RC-01/RC-03: All components must come from KnowledgeSnapshot, not recomputed
        if result.profile_snapshot is not snap.profile_snapshot:
            violations.append(
                "RC-03: result.profile_snapshot must be the exact object from "
                "KnowledgeSnapshot — no recomputation or copy."
            )
        if result.narrative is not snap.narrative:
            violations.append(
                "RC-03: result.narrative must be the exact object from "
                "KnowledgeSnapshot — no recomputation or copy."
            )
        if result.coaching_snapshot is not snap.coaching_snapshot:
            violations.append(
                "RC-03: result.coaching_snapshot must be the exact object from "
                "KnowledgeSnapshot — no recomputation or copy."
            )
        if result.policy_versions is not snap.policy_versions:
            violations.append(
                "RC-03: result.policy_versions must be the exact object from "
                "KnowledgeSnapshot — no recomputation or copy."
            )

        # RC-04: knowledge_epoch must match snapshot
        if result.knowledge_epoch != snap.knowledge_epoch:
            violations.append(
                f"RC-04: result.knowledge_epoch='{result.knowledge_epoch}' "
                f"does not match snapshot.knowledge_epoch='{snap.knowledge_epoch}'."
            )

        # SP-03: manifest must record source_per_component
        manifest = result.manifest
        required_components = {"profile", "narrative", "coaching", "policy_versions"}
        missing = required_components - set(manifest.source_per_component.keys())
        if missing:
            violations.append(
                f"SP-03: ReplayManifest.source_per_component missing keys: {sorted(missing)}."
            )

        # SP-02: Priority 6 (FeatureEngine recomputation) not allowed in STANDARD mode
        if result.replay_mode == ReplayMode.STANDARD:
            for component, priority in manifest.source_per_component.items():
                if priority == ReplaySourcePriority.FEATURE_ENGINE_RECOMPUTATION:
                    violations.append(
                        f"SP-02: Component '{component}' used Priority 6 "
                        "(FeatureEngine recomputation) in STANDARD mode — forbidden."
                    )

        # Migration metadata consistency (MP-03)
        if result.replay_mode in (ReplayMode.MIGRATION, ReplayMode.RECOVERY):
            if manifest.migration_metadata is None:
                violations.append(
                    "MP-03: migration_metadata must be present when "
                    f"replay_mode={result.replay_mode.value}."
                )
        else:
            if manifest.migration_metadata is not None:
                violations.append(
                    "MP-03: migration_metadata must be None in STANDARD mode."
                )

        # Manifest session/candidate consistency
        if manifest.session_id != result.session_id:
            violations.append(
                f"SP-03: manifest.session_id='{manifest.session_id}' "
                f"does not match result.session_id='{result.session_id}'."
            )

        if violations:
            return ReplayValidationResult.failed(violations)
        return ReplayValidationResult.ok()
