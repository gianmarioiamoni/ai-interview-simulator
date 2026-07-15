# domain/contracts/replay/replay_validator.py
# ADR-026 §B4, §C — ReplayValidator (invariant enforcement for Replay layer)
# V1.3: validate_result deleted; validate_session added (RS-V-01..RS-V-10).

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.contracts.replay.replay_context import ReplayContext
from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode, ReplaySourcePriority

if TYPE_CHECKING:
    from domain.contracts.replay.replay_session import ReplaySession


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
    """Validates replay layer invariants for ReplayContext and ReplaySession (V1.3).

    Validates:
    - Context pre-replay invariants
    - Session post-replay invariants RS-V-01 through RS-V-10
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
    # Session validation (V1.3 — post-replay, replaces validate_result)
    # -----------------------------------------------------------------

    @staticmethod
    def validate_session(session: "ReplaySession") -> ReplayValidationResult:
        """Validate a ReplaySession (V1.3) — RS-V-01 through RS-V-10."""
        violations: list[str] = []

        # RS-V-01
        if session.manifest.session_id != session.session_id:
            violations.append(
                f"RS-V-01: manifest.session_id ({session.manifest.session_id!r}) "
                f"must equal session_id ({session.session_id!r})."
            )

        # RS-V-02
        if session.manifest.candidate_identity_id != session.candidate_identity_id:
            violations.append(
                f"RS-V-02: manifest.candidate_identity_id ({session.manifest.candidate_identity_id!r}) "
                f"must equal candidate_identity_id ({session.candidate_identity_id!r})."
            )

        # RS-V-03
        if session.is_successful and session.failure_reason is not None:
            violations.append(
                "RS-V-03: is_successful=True requires failure_reason to be None."
            )

        # RS-V-04
        if not session.is_successful and not session.failure_reason:
            violations.append(
                "RS-V-04: is_successful=False requires a non-empty failure_reason."
            )

        # RS-V-05
        if session.replay_level == ReplayLevel.REASONING:
            violations.append(
                "RS-V-05: replay_level REASONING is reserved and not available in V1.3."
            )

        # RS-V-06
        if (
            session.replay_level == ReplayLevel.PRESENTATION
            and session.observation_store_snapshot is not None
        ):
            violations.append(
                "RS-V-06: observation_store_snapshot must be None for PRESENTATION replay level."
            )

        # RS-V-07
        if len(session.question_results) != session.timeline.total_positions:
            violations.append(
                f"RS-V-07: len(question_results) ({len(session.question_results)}) "
                f"must equal timeline.total_positions ({session.timeline.total_positions})."
            )

        # RS-V-08: all question_index values are unique
        question_indices = [qr.question_index for qr in session.question_results]
        if len(question_indices) != len(set(question_indices)):
            violations.append(
                "RS-V-08: All ReplayQuestionRecord question_index values must be unique."
            )

        # RS-V-09: timeline positions contiguous 0..N-1
        positions = [e.position for e in session.timeline.entries]
        expected_positions = list(range(len(positions)))
        if sorted(positions) != expected_positions:
            violations.append(
                f"RS-V-09: ReplayTimelineEntry.position values must be contiguous 0..N-1. "
                f"Got: {sorted(positions)}."
            )

        # RS-V-10: no FEATURE_ENGINE_RECOMPUTATION in STANDARD mode
        if session.replay_mode == ReplayMode.STANDARD:
            for component, priority in session.manifest.source_per_component.items():
                if priority == ReplaySourcePriority.FEATURE_ENGINE_RECOMPUTATION:
                    violations.append(
                        f"RS-V-10: Component '{component}' used FEATURE_ENGINE_RECOMPUTATION "
                        "in STANDARD mode — forbidden."
                    )

        if violations:
            return ReplayValidationResult.failed(violations)
        return ReplayValidationResult.ok()
