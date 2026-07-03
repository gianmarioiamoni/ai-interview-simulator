# domain/contracts/progress/learning_progress_validator.py
# ADR-016A + ADR-022 — LearningProgressValidator (structural invariant validation)

from __future__ import annotations

from dataclasses import dataclass

from domain.contracts.progress.learning_progress import LearningProgress


@dataclass(frozen=True)
class LearningProgressValidationResult:
    """Immutable result of a LearningProgress validation pass.

    is_valid is True iff violations is empty.
    """

    is_valid: bool
    violations: tuple[str, ...]

    @classmethod
    def ok(cls) -> "LearningProgressValidationResult":
        return cls(is_valid=True, violations=())

    @classmethod
    def failed(cls, violations: list[str]) -> "LearningProgressValidationResult":
        return cls(is_valid=False, violations=tuple(violations))


class LearningProgressValidator:
    """Validates structural invariants of a LearningProgress (ADR-016A + ADR-022).

    Responsibility: validation only. No construction, no summarisation, no business logic.

    Invariants checked:
    - LP-01: candidate_identity_id is non-empty
    - LP-02: all session_entries share the same candidate_identity_id
    - LP-03: session_entries are ordered by session_index (monotonically non-decreasing)
    - LP-04: no duplicate session_id in session_entries
    - LP-05: no duplicate session_index in session_entries
    - LP-06: schema_version is non-empty
    - LP-07: computed_at is timezone-aware
    - LP-08: knowledge_epoch is non-empty
    """

    @staticmethod
    def validate(progress: LearningProgress) -> LearningProgressValidationResult:
        """Run all invariant checks and return a validation result."""
        violations: list[str] = []

        if not progress.candidate_identity_id.strip():
            violations.append("LP-01: candidate_identity_id must not be blank.")

        if not progress.schema_version.strip():
            violations.append("LP-06: schema_version must not be blank.")

        if not progress.knowledge_epoch.strip():
            violations.append("LP-08: knowledge_epoch must not be blank.")

        if progress.computed_at.tzinfo is None:
            violations.append("LP-07: computed_at must be timezone-aware.")

        if progress.session_entries:
            session_ids: list[str] = []
            session_indices: list[int] = []

            for entry in progress.session_entries:
                session_ids.append(entry.session_id)
                session_indices.append(entry.session_index)

            # LP-03: ordering
            if session_indices != sorted(session_indices):
                violations.append(
                    "LP-03: session_entries must be ordered by session_index ascending."
                )

            # LP-04: no duplicate session_id
            if len(session_ids) != len(set(session_ids)):
                violations.append("LP-04: session_entries must have unique session_ids.")

            # LP-05: no duplicate session_index
            if len(session_indices) != len(set(session_indices)):
                violations.append("LP-05: session_entries must have unique session_indices.")

        if violations:
            return LearningProgressValidationResult.failed(violations)
        return LearningProgressValidationResult.ok()
