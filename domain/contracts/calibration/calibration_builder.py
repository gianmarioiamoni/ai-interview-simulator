# domain/contracts/calibration/calibration_builder.py
# EPIC-06 E06-M1 — CalibrationBuilder (sole creation path for CalibrationProfile + CalibrationSnapshot)

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from domain.contracts.calibration.calibration_profile import (
    CalibrationProfile,
    FeatureCalibrationBand,
)
from domain.contracts.calibration.calibration_snapshot import (
    CalibrationSnapshot,
    DimensionCalibrationResult,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot import KnowledgeSnapshot
from domain.contracts.progress.learning_progress import LearningProgress


class CalibrationBuilder:
    """Sole permitted constructor for CalibrationProfile and CalibrationSnapshot.

    Derives both contracts from LearningProgress (history) and an optional
    KnowledgeSnapshot (current session state to evaluate against the profile).

    Rules:
    - Never modifies LearningProgress, KnowledgeSnapshot, or CandidateProfile.
    - All derivation is pure read.
    - candidate_identity_id must be consistent across all inputs.
    - build_profile() produces CalibrationProfile from LearningProgress.
    - build_snapshot() produces CalibrationSnapshot from KnowledgeSnapshot + CalibrationProfile.

    Usage::

        profile = (
            CalibrationBuilder()
            .with_candidate_identity_id(candidate_id)
            .with_role("Software Engineer")
            .with_seniority("Senior")
            .with_learning_progress(progress)
            .build_profile()
        )

        snapshot = (
            CalibrationBuilder()
            .with_candidate_identity_id(candidate_id)
            .with_role("Software Engineer")
            .with_seniority("Senior")
            .with_learning_progress(progress)
            .with_knowledge_snapshot(snapshot)
            .build_snapshot()
        )
    """

    def __init__(self) -> None:
        self._candidate_identity_id: str | None = None
        self._role: str | None = None
        self._seniority: str | None = None
        self._learning_progress: LearningProgress | None = None
        self._knowledge_snapshot: KnowledgeSnapshot | None = None
        self._computed_at: datetime | None = None
        self._knowledge_epoch: str = "1"
        self._schema_version: str = "1.0"
        self._metadata: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Fluent setters
    # ------------------------------------------------------------------

    def with_candidate_identity_id(self, candidate_identity_id: str) -> "CalibrationBuilder":
        self._candidate_identity_id = candidate_identity_id
        return self

    def with_role(self, role: str) -> "CalibrationBuilder":
        self._role = role
        return self

    def with_seniority(self, seniority: str) -> "CalibrationBuilder":
        self._seniority = seniority
        return self

    def with_learning_progress(self, progress: LearningProgress) -> "CalibrationBuilder":
        self._learning_progress = progress
        return self

    def with_knowledge_snapshot(self, snapshot: KnowledgeSnapshot) -> "CalibrationBuilder":
        self._knowledge_snapshot = snapshot
        return self

    def with_computed_at(self, computed_at: datetime) -> "CalibrationBuilder":
        self._computed_at = computed_at
        return self

    def with_knowledge_epoch(self, epoch: str) -> "CalibrationBuilder":
        self._knowledge_epoch = epoch
        return self

    def with_metadata(self, metadata: dict[str, str]) -> "CalibrationBuilder":
        self._metadata = metadata
        return self

    # ------------------------------------------------------------------
    # Terminal — CalibrationProfile
    # ------------------------------------------------------------------

    def build_profile(self) -> CalibrationProfile:
        """Derive and produce an immutable CalibrationProfile.

        Raises:
            ValueError: if mandatory fields are missing or identity is inconsistent.
        """
        self._validate_mandatory_profile_fields()
        assert self._candidate_identity_id is not None
        assert self._role is not None
        assert self._seniority is not None
        assert self._learning_progress is not None

        if self._learning_progress.candidate_identity_id != self._candidate_identity_id:
            raise ValueError(
                f"LearningProgress.candidate_identity_id="
                f"'{self._learning_progress.candidate_identity_id}' does not match "
                f"builder candidate_identity_id='{self._candidate_identity_id}'."
            )

        bands = self._derive_calibration_bands(self._learning_progress, self._seniority)
        computed_at = self._computed_at or datetime.now(tz=timezone.utc)

        return CalibrationProfile(
            candidate_identity_id=self._candidate_identity_id,
            role=self._role,
            seniority=self._seniority,
            knowledge_epoch=self._learning_progress.knowledge_epoch,
            schema_version=self._schema_version,
            feature_bands=tuple(bands),
            session_count_used=self._learning_progress.session_count,
            computed_at=computed_at,
            metadata=self._metadata,
        )

    # ------------------------------------------------------------------
    # Terminal — CalibrationSnapshot
    # ------------------------------------------------------------------

    def build_snapshot(self) -> CalibrationSnapshot:
        """Derive and produce an immutable CalibrationSnapshot.

        Requires: learning_progress + knowledge_snapshot.
        Raises:
            ValueError: if mandatory fields are missing or identity is inconsistent.
        """
        self._validate_mandatory_profile_fields()
        if self._knowledge_snapshot is None:
            raise ValueError(
                "CalibrationBuilder requires knowledge_snapshot to build_snapshot()."
            )

        assert self._candidate_identity_id is not None

        if self._knowledge_snapshot.candidate_identity_id != self._candidate_identity_id:
            raise ValueError(
                f"KnowledgeSnapshot.candidate_identity_id="
                f"'{self._knowledge_snapshot.candidate_identity_id}' does not match "
                f"builder candidate_identity_id='{self._candidate_identity_id}'."
            )

        profile = self.build_profile()
        dimension_results = self._evaluate_against_profile(
            self._knowledge_snapshot, profile
        )

        total = len(dimension_results)
        within = sum(1 for r in dimension_results if r.is_within_band)
        above = sum(1 for r in dimension_results if r.is_above_band)
        below = sum(1 for r in dimension_results if r.is_below_band)
        score = within / total if total > 0 else 0.0

        computed_at = self._computed_at or datetime.now(tz=timezone.utc)

        return CalibrationSnapshot(
            snapshot_id=str(uuid.uuid4()),
            candidate_identity_id=self._candidate_identity_id,
            session_id=self._knowledge_snapshot.session_id,
            role=profile.role,
            seniority=profile.seniority,
            knowledge_epoch=profile.knowledge_epoch,
            schema_version=self._schema_version,
            calibration_profile=profile,
            dimension_results=tuple(dimension_results),
            overall_calibration_score=score,
            dimensions_within_band=within,
            dimensions_above_band=above,
            dimensions_below_band=below,
            computed_at=computed_at,
            metadata=self._metadata,
        )

    # ------------------------------------------------------------------
    # Private derivation helpers — pure read, no mutation
    # ------------------------------------------------------------------

    def _validate_mandatory_profile_fields(self) -> None:
        missing: list[str] = []
        if not self._candidate_identity_id:
            missing.append("candidate_identity_id")
        if not self._role:
            missing.append("role")
        if not self._seniority:
            missing.append("seniority")
        if self._learning_progress is None:
            missing.append("learning_progress")
        if missing:
            raise ValueError(
                f"CalibrationBuilder is missing mandatory fields: {missing}."
            )

    @staticmethod
    def _derive_calibration_bands(
        progress: LearningProgress,
        seniority: str,
    ) -> list[FeatureCalibrationBand]:
        """Derive calibration bands per feature_type_id from LearningProgress.

        Groups DimensionalScore values by feature_type_id across all sessions
        and computes min/max/mean confidence as the expected band.
        """
        from collections import defaultdict

        scores_by_fid: dict[str, list[float]] = defaultdict(list)
        category_by_fid: dict[str, str] = {}

        for entry in progress.session_entries:
            for score in entry.dimensional_scores:
                scores_by_fid[score.feature_type_id].append(score.confidence)
                category_by_fid[score.feature_type_id] = score.semantic_category

        bands: list[FeatureCalibrationBand] = []
        for fid in sorted(scores_by_fid):
            values = scores_by_fid[fid]
            bands.append(FeatureCalibrationBand(
                feature_type_id=fid,
                semantic_category=category_by_fid[fid],
                seniority=seniority,
                expected_min=min(values),
                expected_max=max(values),
                expected_mean=sum(values) / len(values),
                observation_count=len(values),
            ))
        return bands

    @staticmethod
    def _evaluate_against_profile(
        snapshot: KnowledgeSnapshot,
        profile: CalibrationProfile,
    ) -> list[DimensionCalibrationResult]:
        """Compare KnowledgeSnapshot feature confidences against CalibrationProfile bands.

        Pure read. No mutation.
        """
        bands_by_fid = {b.feature_type_id: b for b in profile.feature_bands}
        features = snapshot.profile_snapshot.features
        results: list[DimensionCalibrationResult] = []

        for feature in features:
            fid = feature.feature_identity.feature_type_id
            actual = feature.quality.confidence.value
            band = bands_by_fid.get(fid)
            if band is None:
                continue
            deviation = actual - band.expected_mean
            is_within = band.expected_min <= actual <= band.expected_max
            is_above = actual > band.expected_max
            is_below = actual < band.expected_min
            results.append(DimensionCalibrationResult(
                feature_type_id=fid,
                semantic_category=feature.feature_identity.semantic_category,
                actual_confidence=actual,
                expected_min=band.expected_min,
                expected_max=band.expected_max,
                expected_mean=band.expected_mean,
                deviation=deviation,
                is_within_band=is_within,
                is_above_band=is_above,
                is_below_band=is_below,
            ))
        return results
