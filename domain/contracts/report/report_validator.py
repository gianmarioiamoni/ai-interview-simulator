# domain/contracts/report/report_validator.py
# E03-M5 — ReportValidator (structural invariant validation for Report)
# ADR-023, ADR-025, ADR-032

from __future__ import annotations

from dataclasses import dataclass

from domain.contracts.report.report import Report


@dataclass(frozen=True)
class ReportValidationResult:
    """Immutable result of a Report validation pass.

    is_valid is True iff violations is empty.
    """

    is_valid: bool
    violations: tuple[str, ...]

    @classmethod
    def ok(cls) -> "ReportValidationResult":
        return cls(is_valid=True, violations=())

    @classmethod
    def failed(cls, violations: list[str]) -> "ReportValidationResult":
        return cls(is_valid=False, violations=tuple(violations))


class ReportValidator:
    """Validates structural invariants of a Report (E03-M5).

    Responsibility: validation only. No construction, no summarisation, no business logic.

    Invariants checked:
    - R-01: report_id is non-empty.
    - R-02: session_id and candidate_identity_id are non-empty.
    - R-03: interview_index >= 0.
    - R-04: profile_snapshot.candidate_identity_id matches report.candidate_identity_id.
    - R-05: narrative is complete (all 5 mandatory sections present).
    - R-06: knowledge_epoch is non-empty.
    - R-07: schema_version is non-empty.
    - R-08: created_at is timezone-aware.
    - R-09: question_count >= 0.
    - R-10: role, seniority, interview_type are non-blank.
    """

    @staticmethod
    def validate(report: Report) -> ReportValidationResult:
        """Run all invariant checks and return a validation result."""
        violations: list[str] = []

        if not report.report_id.strip():
            violations.append("R-01: report_id must not be blank.")

        if not report.session_id.strip():
            violations.append("R-02: session_id must not be blank.")

        if not report.candidate_identity_id.strip():
            violations.append("R-02: candidate_identity_id must not be blank.")

        if report.interview_index < 0:
            violations.append("R-03: interview_index must be >= 0.")

        if report.profile_snapshot.candidate_identity_id != report.candidate_identity_id:
            violations.append(
                f"R-04: profile_snapshot.candidate_identity_id="
                f"'{report.profile_snapshot.candidate_identity_id}' "
                f"does not match report.candidate_identity_id='{report.candidate_identity_id}'."
            )

        if not report.narrative.is_complete:
            violations.append("R-05: Narrative is incomplete — all 5 sections are mandatory.")

        if not report.knowledge_epoch.strip():
            violations.append("R-06: knowledge_epoch must not be blank.")

        if not report.schema_version.strip():
            violations.append("R-07: schema_version must not be blank.")

        if report.created_at.tzinfo is None:
            violations.append("R-08: created_at must be timezone-aware.")

        if report.question_count < 0:
            violations.append("R-09: question_count must be >= 0.")

        if not report.role.strip():
            violations.append("R-10: role must not be blank.")

        if not report.seniority.strip():
            violations.append("R-10: seniority must not be blank.")

        if not report.interview_type.strip():
            violations.append("R-10: interview_type must not be blank.")

        if violations:
            return ReportValidationResult.failed(violations)
        return ReportValidationResult.ok()
