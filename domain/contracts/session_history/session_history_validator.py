# domain/contracts/session_history/session_history_validator.py
# ADR-022 — SessionHistoryValidator (structural and invariant validation)

from __future__ import annotations

from dataclasses import dataclass

from domain.contracts.session_history.session_history import SessionHistory


@dataclass(frozen=True)
class SessionHistoryValidationResult:
    """Immutable result of a SessionHistory validation pass.

    is_valid is True iff violations is empty.
    """

    is_valid: bool
    violations: tuple[str, ...]

    @classmethod
    def ok(cls) -> "SessionHistoryValidationResult":
        return cls(is_valid=True, violations=())

    @classmethod
    def failed(cls, violations: list[str]) -> "SessionHistoryValidationResult":
        return cls(is_valid=False, violations=tuple(violations))


class SessionHistoryValidator:
    """Validates structural and knowledge invariants of a SessionHistory (ADR-022).

    Responsibility: validation only. No construction, no summarisation, no business logic.

    Invariants checked:
    - SH-01: session_id is non-empty
    - SH-02: candidate_identity_id is non-empty
    - SH-03: interview_index >= 0
    - SH-04: knowledge_snapshot.candidate_identity_id matches history.candidate_identity_id
    - SH-05: knowledge_snapshot.session_id matches history.session_id
    - SH-06: language_profile.session_id matches history.session_id
    - SH-07: schema_version is non-empty
    - SH-08: created_at is a timezone-aware datetime
    - SH-09: transcript entries are ordered by question_index (monotonically non-decreasing)
    - SH-10: question_timeline entries are ordered by question_index (monotonically non-decreasing)
    """

    @staticmethod
    def validate(history: SessionHistory) -> SessionHistoryValidationResult:
        """Run all invariant checks and return a validation result."""
        violations: list[str] = []

        if not history.session_id.strip():
            violations.append("SH-01: session_id must not be blank.")

        if not history.candidate_identity_id.strip():
            violations.append("SH-02: candidate_identity_id must not be blank.")

        if history.interview_index < 0:
            violations.append("SH-03: interview_index must be >= 0.")

        if history.knowledge_snapshot.candidate_identity_id != history.candidate_identity_id:
            violations.append(
                f"SH-04: knowledge_snapshot.candidate_identity_id="
                f"'{history.knowledge_snapshot.candidate_identity_id}' "
                f"does not match history.candidate_identity_id='{history.candidate_identity_id}'."
            )

        if history.knowledge_snapshot.session_id != history.session_id:
            violations.append(
                f"SH-05: knowledge_snapshot.session_id="
                f"'{history.knowledge_snapshot.session_id}' "
                f"does not match history.session_id='{history.session_id}'."
            )

        if history.language_profile.session_id != history.session_id:
            violations.append(
                f"SH-06: language_profile.session_id="
                f"'{history.language_profile.session_id}' "
                f"does not match history.session_id='{history.session_id}'."
            )

        if not history.schema_version.strip():
            violations.append("SH-07: schema_version must not be blank.")

        if history.created_at.tzinfo is None:
            violations.append("SH-08: created_at must be timezone-aware.")

        # SH-09: transcript ordering
        if history.transcript:
            indices = [e.question_index for e in history.transcript]
            if indices != sorted(indices):
                violations.append(
                    "SH-09: transcript entries must be ordered by question_index."
                )

        # SH-10: timeline ordering
        if history.question_timeline:
            indices = [e.question_index for e in history.question_timeline]
            if indices != sorted(indices):
                violations.append(
                    "SH-10: question_timeline entries must be ordered by question_index."
                )

        if violations:
            return SessionHistoryValidationResult.failed(violations)
        return SessionHistoryValidationResult.ok()
