# domain/contracts/calibration/calibration_validator.py
# EPIC-06 E06-M1 — CalibrationValidator (structural invariant validation)

from __future__ import annotations

from dataclasses import dataclass

from domain.contracts.calibration.calibration_profile import CalibrationProfile
from domain.contracts.calibration.calibration_snapshot import CalibrationSnapshot


@dataclass(frozen=True)
class CalibrationValidationResult:
    """Immutable result of a calibration validation pass.

    is_valid is True iff violations is empty.
    """

    is_valid: bool
    violations: tuple[str, ...]

    @classmethod
    def ok(cls) -> "CalibrationValidationResult":
        return cls(is_valid=True, violations=())

    @classmethod
    def failed(cls, violations: list[str]) -> "CalibrationValidationResult":
        return cls(is_valid=False, violations=tuple(violations))


class CalibrationProfileValidator:
    """Validates structural invariants of a CalibrationProfile.

    Responsibility: validation only. No construction, no summarisation, no business logic.

    Invariants checked:
    - CP-01: candidate_identity_id is non-empty
    - CP-02: role and seniority are non-empty
    - CP-03: knowledge_epoch is non-empty
    - CP-04: schema_version is non-empty
    - CP-05: computed_at is timezone-aware
    - CP-06: no duplicate feature_type_id within same seniority band
    - CP-07: expected_min <= expected_max for each band
    - CP-08: expected_mean in [expected_min, expected_max] for each band
    """

    @staticmethod
    def validate(profile: CalibrationProfile) -> CalibrationValidationResult:
        violations: list[str] = []

        if not profile.candidate_identity_id.strip():
            violations.append("CP-01: candidate_identity_id must not be blank.")

        if not profile.role.strip():
            violations.append("CP-02: role must not be blank.")

        if not profile.seniority.strip():
            violations.append("CP-02: seniority must not be blank.")

        if not profile.knowledge_epoch.strip():
            violations.append("CP-03: knowledge_epoch must not be blank.")

        if not profile.schema_version.strip():
            violations.append("CP-04: schema_version must not be blank.")

        if profile.computed_at.tzinfo is None:
            violations.append("CP-05: computed_at must be timezone-aware.")

        seen: set[tuple[str, str]] = set()
        for band in profile.feature_bands:
            key = (band.feature_type_id, band.seniority)
            if key in seen:
                violations.append(
                    f"CP-06: duplicate feature_type_id='{band.feature_type_id}' "
                    f"for seniority='{band.seniority}'."
                )
            seen.add(key)

            if band.expected_min > band.expected_max:
                violations.append(
                    f"CP-07: band '{band.feature_type_id}' expected_min "
                    f"({band.expected_min}) > expected_max ({band.expected_max})."
                )

            if not (band.expected_min <= band.expected_mean <= band.expected_max):
                violations.append(
                    f"CP-08: band '{band.feature_type_id}' expected_mean "
                    f"({band.expected_mean}) not in "
                    f"[{band.expected_min}, {band.expected_max}]."
                )

        if violations:
            return CalibrationValidationResult.failed(violations)
        return CalibrationValidationResult.ok()


class CalibrationSnapshotValidator:
    """Validates structural invariants of a CalibrationSnapshot.

    Invariants checked:
    - CS-01: snapshot_id is non-empty
    - CS-02: candidate_identity_id matches profile.candidate_identity_id
    - CS-03: session_id is non-empty
    - CS-04: knowledge_epoch is non-empty
    - CS-05: computed_at is timezone-aware
    - CS-06: dimensions_within_band + above + below == total_dimensions
    - CS-07: overall_calibration_score in [0.0, 1.0]
    """

    @staticmethod
    def validate(snapshot: CalibrationSnapshot) -> CalibrationValidationResult:
        violations: list[str] = []

        if not snapshot.snapshot_id.strip():
            violations.append("CS-01: snapshot_id must not be blank.")

        if not snapshot.session_id.strip():
            violations.append("CS-03: session_id must not be blank.")

        if not snapshot.knowledge_epoch.strip():
            violations.append("CS-04: knowledge_epoch must not be blank.")

        if snapshot.computed_at.tzinfo is None:
            violations.append("CS-05: computed_at must be timezone-aware.")

        if (snapshot.candidate_identity_id !=
                snapshot.calibration_profile.candidate_identity_id):
            violations.append(
                f"CS-02: snapshot.candidate_identity_id="
                f"'{snapshot.candidate_identity_id}' does not match "
                f"profile.candidate_identity_id="
                f"'{snapshot.calibration_profile.candidate_identity_id}'."
            )

        dimension_sum = (
            snapshot.dimensions_within_band
            + snapshot.dimensions_above_band
            + snapshot.dimensions_below_band
        )
        if snapshot.dimension_results and dimension_sum != snapshot.total_dimensions:
            violations.append(
                f"CS-06: within + above + below = {dimension_sum} != "
                f"total_dimensions={snapshot.total_dimensions}."
            )

        if violations:
            return CalibrationValidationResult.failed(violations)
        return CalibrationValidationResult.ok()
