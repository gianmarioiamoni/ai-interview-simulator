# domain/contracts/knowledge_snapshot/knowledge_snapshot_validator.py
# ADR-022 — KnowledgeSnapshotValidator (structural and policy invariant validation)

from __future__ import annotations

from dataclasses import dataclass, field

from domain.contracts.knowledge_snapshot.knowledge_snapshot import KnowledgeSnapshot


@dataclass(frozen=True)
class KnowledgeSnapshotValidationResult:
    """Immutable result of a KnowledgeSnapshot validation pass.

    is_valid is True iff violations is empty.
    """

    is_valid: bool
    violations: tuple[str, ...]

    @classmethod
    def ok(cls) -> "KnowledgeSnapshotValidationResult":
        return cls(is_valid=True, violations=())

    @classmethod
    def failed(cls, violations: list[str]) -> "KnowledgeSnapshotValidationResult":
        return cls(is_valid=False, violations=tuple(violations))


class KnowledgeSnapshotValidator:
    """Validates structural and policy invariants of a KnowledgeSnapshot (ADR-022).

    Responsibility: validation only. No construction, no summarisation, no business logic.

    Invariants checked:
    - K-01: snapshot_id is non-empty
    - K-03: all policy versions are non-empty strings
    - K-04: knowledge_epoch is non-empty
    - K-07: session_id and candidate_identity_id are consistent
    - K-09: profile_snapshot.candidate_identity_id matches snapshot.candidate_identity_id
    - K-10: narrative has all 5 mandatory sections (is_complete)
    - Coaching session_id matches snapshot.session_id
    """

    @staticmethod
    def validate(snapshot: KnowledgeSnapshot) -> KnowledgeSnapshotValidationResult:
        """Run all invariant checks and return a validation result."""
        violations: list[str] = []

        # K-01: snapshot_id non-empty
        if not snapshot.snapshot_id.strip():
            violations.append("K-01: snapshot_id must not be blank.")

        # K-04: knowledge_epoch non-empty
        if not snapshot.knowledge_epoch.strip():
            violations.append("K-04: knowledge_epoch must not be blank.")

        # K-07: session_id and candidate_identity_id non-empty
        if not snapshot.session_id.strip():
            violations.append("K-07: session_id must not be blank.")
        if not snapshot.candidate_identity_id.strip():
            violations.append("K-07: candidate_identity_id must not be blank.")

        # K-09: profile_snapshot identity must match snapshot identity
        if snapshot.profile_snapshot.candidate_identity_id != snapshot.candidate_identity_id:
            violations.append(
                f"K-09: profile_snapshot.candidate_identity_id="
                f"'{snapshot.profile_snapshot.candidate_identity_id}' "
                f"does not match snapshot.candidate_identity_id='{snapshot.candidate_identity_id}'."
            )

        # K-10: narrative must be complete
        if not snapshot.narrative.is_complete:
            violations.append("K-10: Narrative is incomplete — all 5 sections are mandatory.")

        # K-03: policy versions all non-empty
        pv = snapshot.policy_versions
        policy_checks = {
            "feature_engine_version": pv.feature_engine_version,
            "language_policy_version": pv.language_policy_version,
            "ttl_policy_version": pv.ttl_policy_version,
            "evaluation_policy_version": pv.evaluation_policy_version,
            "narrative_schema_version": pv.narrative_schema_version,
            "coaching_schema_version": pv.coaching_schema_version,
            "profile_schema_version": pv.profile_schema_version,
        }
        for version_field, version_value in policy_checks.items():
            if not version_value.strip():
                violations.append(f"K-03: policy_versions.{version_field} must not be blank.")

        # Coaching session_id consistency
        if snapshot.coaching_snapshot.session_id != snapshot.session_id:
            violations.append(
                f"Coaching session_id='{snapshot.coaching_snapshot.session_id}' "
                f"does not match snapshot session_id='{snapshot.session_id}'."
            )

        if violations:
            return KnowledgeSnapshotValidationResult.failed(violations)
        return KnowledgeSnapshotValidationResult.ok()
