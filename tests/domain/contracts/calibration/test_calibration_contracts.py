# tests/domain/contracts/calibration/test_calibration_contracts.py
# Contract, validation, architecture, integration, and determinism tests for EPIC-06 E06-M1

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.contracts.calibration.calibration_builder import CalibrationBuilder
from domain.contracts.calibration.calibration_metrics import CalibrationMetrics
from domain.contracts.calibration.calibration_profile import CalibrationProfile, FeatureCalibrationBand
from domain.contracts.calibration.calibration_snapshot import CalibrationSnapshot
from domain.contracts.calibration.calibration_statistics import CalibrationStatistics
from domain.contracts.calibration.calibration_summary import CalibrationSummary
from domain.contracts.calibration.calibration_validator import (
    CalibrationProfileValidator,
    CalibrationSnapshotValidator,
    CalibrationValidationResult,
)
from tests.domain.contracts.calibration.conftest import (
    CANDIDATE_ID,
    ROLE,
    SENIORITY,
    FIXED_COMPUTED_AT,
    make_calibration_profile,
    make_calibration_snapshot,
)
from tests.domain.contracts.knowledge_snapshot.conftest import (
    SESSION_ID,
    make_knowledge_snapshot,
)
from tests.domain.contracts.progress.conftest import (
    CANDIDATE_ID_B,
    make_learning_progress,
)


# ===========================================================================
# CONTRACT TESTS — CalibrationProfile
# ===========================================================================

class TestCalibrationProfileContract:
    def test_profile_is_immutable(self, calibration_profile: CalibrationProfile) -> None:
        with pytest.raises(Exception):
            calibration_profile.candidate_identity_id = "x"  # type: ignore[misc]

    def test_profile_candidate_identity_id(self, calibration_profile: CalibrationProfile) -> None:
        assert calibration_profile.candidate_identity_id == CANDIDATE_ID

    def test_profile_role_seniority(self, calibration_profile: CalibrationProfile) -> None:
        assert calibration_profile.role == ROLE
        assert calibration_profile.seniority == SENIORITY

    def test_profile_feature_bands_non_empty(self, calibration_profile: CalibrationProfile) -> None:
        assert len(calibration_profile.feature_bands) > 0

    def test_profile_bands_are_immutable(self, calibration_profile: CalibrationProfile) -> None:
        band = calibration_profile.feature_bands[0]
        with pytest.raises(Exception):
            band.feature_type_id = "x"  # type: ignore[misc]

    def test_profile_empty_when_no_sessions(
        self, empty_progress_profile: CalibrationProfile
    ) -> None:
        assert empty_progress_profile.is_empty
        assert empty_progress_profile.feature_bands == ()

    def test_profile_feature_type_ids_property(self, calibration_profile: CalibrationProfile) -> None:
        ids = calibration_profile.feature_type_ids
        assert isinstance(ids, frozenset)
        assert len(ids) == len(calibration_profile.feature_bands)

    def test_band_min_le_max(self, calibration_profile: CalibrationProfile) -> None:
        for band in calibration_profile.feature_bands:
            assert band.expected_min <= band.expected_max

    def test_band_mean_in_range(self, calibration_profile: CalibrationProfile) -> None:
        for band in calibration_profile.feature_bands:
            assert band.expected_min <= band.expected_mean <= band.expected_max


# ===========================================================================
# CONTRACT TESTS — CalibrationSnapshot
# ===========================================================================

class TestCalibrationSnapshotContract:
    def test_snapshot_is_immutable(self, calibration_snapshot: CalibrationSnapshot) -> None:
        with pytest.raises(Exception):
            calibration_snapshot.snapshot_id = "x"  # type: ignore[misc]

    def test_snapshot_candidate_id(self, calibration_snapshot: CalibrationSnapshot) -> None:
        assert calibration_snapshot.candidate_identity_id == CANDIDATE_ID

    def test_snapshot_session_id(self, calibration_snapshot: CalibrationSnapshot) -> None:
        assert calibration_snapshot.session_id == SESSION_ID

    def test_snapshot_dimension_results(self, calibration_snapshot: CalibrationSnapshot) -> None:
        assert len(calibration_snapshot.dimension_results) > 0

    def test_snapshot_dimension_results_immutable(
        self, calibration_snapshot: CalibrationSnapshot
    ) -> None:
        r = calibration_snapshot.dimension_results[0]
        with pytest.raises(Exception):
            r.feature_type_id = "x"  # type: ignore[misc]

    def test_snapshot_overall_score_in_range(
        self, calibration_snapshot: CalibrationSnapshot
    ) -> None:
        assert 0.0 <= calibration_snapshot.overall_calibration_score <= 1.0

    def test_snapshot_dimension_counts_sum(self, calibration_snapshot: CalibrationSnapshot) -> None:
        total = (
            calibration_snapshot.dimensions_within_band
            + calibration_snapshot.dimensions_above_band
            + calibration_snapshot.dimensions_below_band
        )
        assert total == calibration_snapshot.total_dimensions

    def test_snapshot_knowledge_epoch(self, calibration_snapshot: CalibrationSnapshot) -> None:
        assert calibration_snapshot.knowledge_epoch == "1"

    def test_snapshot_is_fully_calibrated_property(
        self, calibration_snapshot: CalibrationSnapshot
    ) -> None:
        if calibration_snapshot.dimensions_within_band == calibration_snapshot.total_dimensions:
            assert calibration_snapshot.is_fully_calibrated
        else:
            assert not calibration_snapshot.is_fully_calibrated


# ===========================================================================
# BUILDER TESTS
# ===========================================================================

class TestCalibrationBuilder:
    def test_builder_is_sole_creation_path_profile(self) -> None:
        progress = make_learning_progress()
        profile = (
            CalibrationBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_role(ROLE)
            .with_seniority(SENIORITY)
            .with_learning_progress(progress)
            .with_computed_at(FIXED_COMPUTED_AT)
            .build_profile()
        )
        assert profile.candidate_identity_id == CANDIDATE_ID

    def test_builder_raises_without_candidate_id(self) -> None:
        progress = make_learning_progress()
        with pytest.raises(ValueError, match="candidate_identity_id"):
            (
                CalibrationBuilder()
                .with_role(ROLE)
                .with_seniority(SENIORITY)
                .with_learning_progress(progress)
                .build_profile()
            )

    def test_builder_raises_without_role(self) -> None:
        progress = make_learning_progress()
        with pytest.raises(ValueError, match="role"):
            (
                CalibrationBuilder()
                .with_candidate_identity_id(CANDIDATE_ID)
                .with_seniority(SENIORITY)
                .with_learning_progress(progress)
                .build_profile()
            )

    def test_builder_raises_without_progress(self) -> None:
        with pytest.raises(ValueError, match="learning_progress"):
            (
                CalibrationBuilder()
                .with_candidate_identity_id(CANDIDATE_ID)
                .with_role(ROLE)
                .with_seniority(SENIORITY)
                .build_profile()
            )

    def test_builder_raises_on_foreign_progress(self) -> None:
        foreign_progress = make_learning_progress(candidate_id=CANDIDATE_ID_B)
        with pytest.raises(ValueError, match=CANDIDATE_ID_B):
            (
                CalibrationBuilder()
                .with_candidate_identity_id(CANDIDATE_ID)
                .with_role(ROLE)
                .with_seniority(SENIORITY)
                .with_learning_progress(foreign_progress)
                .build_profile()
            )

    def test_builder_raises_snapshot_without_ks(self) -> None:
        progress = make_learning_progress()
        with pytest.raises(ValueError, match="knowledge_snapshot"):
            (
                CalibrationBuilder()
                .with_candidate_identity_id(CANDIDATE_ID)
                .with_role(ROLE)
                .with_seniority(SENIORITY)
                .with_learning_progress(progress)
                .build_snapshot()
            )

    def test_builder_raises_on_foreign_knowledge_snapshot(self) -> None:
        progress = make_learning_progress()
        foreign_ks = make_knowledge_snapshot(candidate_id=CANDIDATE_ID_B)
        with pytest.raises(ValueError, match=CANDIDATE_ID_B):
            (
                CalibrationBuilder()
                .with_candidate_identity_id(CANDIDATE_ID)
                .with_role(ROLE)
                .with_seniority(SENIORITY)
                .with_learning_progress(progress)
                .with_knowledge_snapshot(foreign_ks)
                .build_snapshot()
            )

    def test_builder_never_modifies_learning_progress(self) -> None:
        progress = make_learning_progress()
        original_count = progress.session_count
        _ = (
            CalibrationBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_role(ROLE)
            .with_seniority(SENIORITY)
            .with_learning_progress(progress)
            .build_profile()
        )
        assert progress.session_count == original_count

    def test_computed_at_defaults_to_now_utc(self) -> None:
        progress = make_learning_progress()
        profile = (
            CalibrationBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_role(ROLE)
            .with_seniority(SENIORITY)
            .with_learning_progress(progress)
            .build_profile()
        )
        assert profile.computed_at.tzinfo is not None


# ===========================================================================
# VALIDATION TESTS
# ===========================================================================

class TestCalibrationProfileValidator:
    def test_valid_profile_passes(self, calibration_profile: CalibrationProfile) -> None:
        result = CalibrationProfileValidator.validate(calibration_profile)
        assert result.is_valid
        assert result.violations == ()

    def test_empty_profile_passes(self, empty_progress_profile: CalibrationProfile) -> None:
        result = CalibrationProfileValidator.validate(empty_progress_profile)
        assert result.is_valid

    def test_blank_candidate_id_fails(self) -> None:
        profile = CalibrationProfile(
            candidate_identity_id="  ",
            role=ROLE,
            seniority=SENIORITY,
            session_count_used=0,
            computed_at=FIXED_COMPUTED_AT,
        )
        result = CalibrationProfileValidator.validate(profile)
        assert not result.is_valid
        assert any("CP-01" in v for v in result.violations)

    def test_naive_computed_at_fails(self) -> None:
        profile = CalibrationProfile(
            candidate_identity_id=CANDIDATE_ID,
            role=ROLE,
            seniority=SENIORITY,
            session_count_used=0,
            computed_at=datetime(2026, 7, 3),  # no tzinfo
        )
        result = CalibrationProfileValidator.validate(profile)
        assert not result.is_valid
        assert any("CP-05" in v for v in result.violations)

    def test_band_min_gt_max_fails(self) -> None:
        band = FeatureCalibrationBand(
            feature_type_id="reasoning_feature",
            semantic_category="analytical_reasoning",
            seniority=SENIORITY,
            expected_min=0.8,
            expected_max=0.3,
            expected_mean=0.5,
            observation_count=2,
        )
        profile = CalibrationProfile(
            candidate_identity_id=CANDIDATE_ID,
            role=ROLE,
            seniority=SENIORITY,
            feature_bands=(band,),
            session_count_used=1,
            computed_at=FIXED_COMPUTED_AT,
        )
        result = CalibrationProfileValidator.validate(profile)
        assert not result.is_valid
        assert any("CP-07" in v for v in result.violations)

    def test_band_mean_outside_range_fails(self) -> None:
        band = FeatureCalibrationBand(
            feature_type_id="reasoning_feature",
            semantic_category="analytical_reasoning",
            seniority=SENIORITY,
            expected_min=0.2,
            expected_max=0.6,
            expected_mean=0.9,
            observation_count=2,
        )
        profile = CalibrationProfile(
            candidate_identity_id=CANDIDATE_ID,
            role=ROLE,
            seniority=SENIORITY,
            feature_bands=(band,),
            session_count_used=1,
            computed_at=FIXED_COMPUTED_AT,
        )
        result = CalibrationProfileValidator.validate(profile)
        assert not result.is_valid
        assert any("CP-08" in v for v in result.violations)

    def test_duplicate_band_fails(self) -> None:
        band = FeatureCalibrationBand(
            feature_type_id="reasoning_feature",
            semantic_category="analytical_reasoning",
            seniority=SENIORITY,
            expected_min=0.5,
            expected_max=0.8,
            expected_mean=0.65,
            observation_count=2,
        )
        profile = CalibrationProfile(
            candidate_identity_id=CANDIDATE_ID,
            role=ROLE,
            seniority=SENIORITY,
            feature_bands=(band, band),
            session_count_used=1,
            computed_at=FIXED_COMPUTED_AT,
        )
        result = CalibrationProfileValidator.validate(profile)
        assert not result.is_valid
        assert any("CP-06" in v for v in result.violations)


class TestCalibrationSnapshotValidator:
    def test_valid_snapshot_passes(self, calibration_snapshot: CalibrationSnapshot) -> None:
        result = CalibrationSnapshotValidator.validate(calibration_snapshot)
        assert result.is_valid

    def test_blank_snapshot_id_fails(self, calibration_snapshot: CalibrationSnapshot) -> None:
        snap = calibration_snapshot.model_copy(update={"snapshot_id": "  "})
        result = CalibrationSnapshotValidator.validate(snap)
        assert not result.is_valid
        assert any("CS-01" in v for v in result.violations)

    def test_identity_mismatch_fails(self, calibration_snapshot: CalibrationSnapshot) -> None:
        snap = calibration_snapshot.model_copy(
            update={"candidate_identity_id": CANDIDATE_ID_B}
        )
        result = CalibrationSnapshotValidator.validate(snap)
        assert not result.is_valid
        assert any("CS-02" in v for v in result.violations)

    def test_naive_computed_at_fails(self, calibration_snapshot: CalibrationSnapshot) -> None:
        snap = calibration_snapshot.model_copy(
            update={"computed_at": datetime(2026, 7, 3)}
        )
        result = CalibrationSnapshotValidator.validate(snap)
        assert not result.is_valid
        assert any("CS-05" in v for v in result.violations)

    def test_validation_result_ok(self) -> None:
        result = CalibrationValidationResult.ok()
        assert result.is_valid
        assert result.violations == ()

    def test_validation_result_failed(self) -> None:
        result = CalibrationValidationResult.failed(["CP-01: x"])
        assert not result.is_valid
        assert len(result.violations) == 1


# ===========================================================================
# STATISTICS TESTS
# ===========================================================================

class TestCalibrationStatistics:
    def test_statistics_from_profile(self, calibration_profile: CalibrationProfile) -> None:
        stats = CalibrationStatistics.from_profile(calibration_profile)
        assert stats.candidate_identity_id == CANDIDATE_ID
        assert stats.total_feature_bands == len(calibration_profile.feature_bands)
        assert not stats.is_empty

    def test_statistics_from_empty_profile(
        self, empty_progress_profile: CalibrationProfile
    ) -> None:
        stats = CalibrationStatistics.from_profile(empty_progress_profile)
        assert stats.is_empty
        assert stats.total_feature_bands == 0

    def test_statistics_mean_values_in_range(
        self, calibration_profile: CalibrationProfile
    ) -> None:
        stats = CalibrationStatistics.from_profile(calibration_profile)
        assert 0.0 <= stats.mean_expected_min <= 1.0
        assert 0.0 <= stats.mean_expected_max <= 1.0
        assert 0.0 <= stats.mean_expected_mean <= 1.0
        assert stats.mean_band_width >= 0.0

    def test_statistics_is_immutable(self, calibration_profile: CalibrationProfile) -> None:
        stats = CalibrationStatistics.from_profile(calibration_profile)
        with pytest.raises(Exception):
            stats.total_feature_bands = 99  # type: ignore[misc]


# ===========================================================================
# SUMMARY TESTS
# ===========================================================================

class TestCalibrationSummary:
    def test_summary_from_snapshot(self, calibration_snapshot: CalibrationSnapshot) -> None:
        summary = CalibrationSummary.from_snapshot(calibration_snapshot)
        assert summary.candidate_identity_id == CANDIDATE_ID
        assert summary.session_id == SESSION_ID
        assert summary.snapshot_id == calibration_snapshot.snapshot_id

    def test_summary_is_immutable(self, calibration_snapshot: CalibrationSnapshot) -> None:
        summary = CalibrationSummary.from_snapshot(calibration_snapshot)
        with pytest.raises(Exception):
            summary.snapshot_id = "x"  # type: ignore[misc]

    def test_summary_score_matches_snapshot(
        self, calibration_snapshot: CalibrationSnapshot
    ) -> None:
        summary = CalibrationSummary.from_snapshot(calibration_snapshot)
        assert summary.overall_calibration_score == calibration_snapshot.overall_calibration_score

    def test_summary_fully_calibrated_flag(
        self, calibration_snapshot: CalibrationSnapshot
    ) -> None:
        summary = CalibrationSummary.from_snapshot(calibration_snapshot)
        assert summary.is_fully_calibrated == calibration_snapshot.is_fully_calibrated


# ===========================================================================
# METRICS TESTS
# ===========================================================================

class TestCalibrationMetrics:
    def test_metrics_from_snapshot(self, calibration_snapshot: CalibrationSnapshot) -> None:
        metrics = CalibrationMetrics.from_snapshot(calibration_snapshot)
        assert metrics.candidate_identity_id == CANDIDATE_ID
        assert metrics.total_dimensions == calibration_snapshot.total_dimensions
        assert not metrics.is_empty

    def test_metrics_absolute_deviations_non_negative(
        self, calibration_snapshot: CalibrationSnapshot
    ) -> None:
        metrics = CalibrationMetrics.from_snapshot(calibration_snapshot)
        assert metrics.mean_absolute_deviation >= 0.0
        assert metrics.max_absolute_deviation >= 0.0

    def test_metrics_dimension_status_valid_values(
        self, calibration_snapshot: CalibrationSnapshot
    ) -> None:
        metrics = CalibrationMetrics.from_snapshot(calibration_snapshot)
        for dm in metrics.dimension_metrics:
            assert dm.status in ("within", "above", "below")

    def test_metrics_is_immutable(self, calibration_snapshot: CalibrationSnapshot) -> None:
        metrics = CalibrationMetrics.from_snapshot(calibration_snapshot)
        with pytest.raises(Exception):
            metrics.total_dimensions = 99  # type: ignore[misc]


# ===========================================================================
# ARCHITECTURE / DERIVATION TESTS
# ===========================================================================

class TestArchitectureInvariants:
    def test_calibration_profile_no_persistence_id(
        self, calibration_profile: CalibrationProfile
    ) -> None:
        assert not hasattr(calibration_profile, "profile_id")

    def test_calibration_snapshot_no_persistence_id(
        self, calibration_snapshot: CalibrationSnapshot
    ) -> None:
        assert hasattr(calibration_snapshot, "snapshot_id")
        assert not hasattr(calibration_snapshot, "persisted_at")

    def test_no_duplicate_calibration_contracts(self) -> None:
        from domain.contracts.calibration import (
            CalibrationProfile, CalibrationSnapshot, CalibrationMetrics,
            CalibrationStatistics, CalibrationSummary,
        )
        assert CalibrationProfile is not CalibrationSnapshot
        assert CalibrationMetrics is not CalibrationStatistics
        assert CalibrationSummary is not CalibrationStatistics

    def test_calibration_derived_from_history_only(self) -> None:
        progress = make_learning_progress()
        profile = (
            CalibrationBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_role(ROLE)
            .with_seniority(SENIORITY)
            .with_learning_progress(progress)
            .build_profile()
        )
        assert profile.session_count_used == progress.session_count

    def test_feature_engine_not_modified(self) -> None:
        """CalibrationBuilder reads ProfileFeature values only — does not call FeatureEngine."""
        progress = make_learning_progress()
        original_entries = list(progress.session_entries)
        _ = make_calibration_profile(progress=progress)
        assert list(progress.session_entries) == original_entries

    def test_knowledge_epoch_preserved(self, calibration_profile: CalibrationProfile) -> None:
        assert calibration_profile.knowledge_epoch == "1"


# ===========================================================================
# DETERMINISM TESTS
# ===========================================================================

class TestDeterminism:
    def test_same_progress_same_band_count(self) -> None:
        progress = make_learning_progress()
        p1 = make_calibration_profile(progress=progress)
        p2 = make_calibration_profile(progress=progress)
        assert len(p1.feature_bands) == len(p2.feature_bands)

    def test_same_inputs_same_band_values(self) -> None:
        progress = make_learning_progress()
        p1 = make_calibration_profile(progress=progress)
        p2 = make_calibration_profile(progress=progress)
        bands1 = {b.feature_type_id: b for b in p1.feature_bands}
        bands2 = {b.feature_type_id: b for b in p2.feature_bands}
        for fid in bands1:
            assert bands1[fid].expected_mean == bands2[fid].expected_mean

    def test_same_inputs_same_snapshot_score(self) -> None:
        progress = make_learning_progress()
        ks = make_knowledge_snapshot(session_id=SESSION_ID, candidate_id=CANDIDATE_ID)
        s1 = (
            CalibrationBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_role(ROLE)
            .with_seniority(SENIORITY)
            .with_learning_progress(progress)
            .with_knowledge_snapshot(ks)
            .with_computed_at(FIXED_COMPUTED_AT)
            .build_snapshot()
        )
        s2 = (
            CalibrationBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_role(ROLE)
            .with_seniority(SENIORITY)
            .with_learning_progress(progress)
            .with_knowledge_snapshot(ks)
            .with_computed_at(FIXED_COMPUTED_AT)
            .build_snapshot()
        )
        assert s1.overall_calibration_score == s2.overall_calibration_score

    def test_statistics_are_deterministic(
        self, calibration_profile: CalibrationProfile
    ) -> None:
        s1 = CalibrationStatistics.from_profile(calibration_profile)
        s2 = CalibrationStatistics.from_profile(calibration_profile)
        assert s1.mean_expected_mean == s2.mean_expected_mean


# ===========================================================================
# INTEGRATION TESTS
# ===========================================================================

class TestIntegration:
    def test_full_pipeline_profile_to_summary(self) -> None:
        progress = make_learning_progress()
        ks = make_knowledge_snapshot(session_id=SESSION_ID, candidate_id=CANDIDATE_ID)
        snapshot = (
            CalibrationBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_role(ROLE)
            .with_seniority(SENIORITY)
            .with_learning_progress(progress)
            .with_knowledge_snapshot(ks)
            .with_computed_at(FIXED_COMPUTED_AT)
            .build_snapshot()
        )
        assert CalibrationSnapshotValidator.validate(snapshot).is_valid
        metrics = CalibrationMetrics.from_snapshot(snapshot)
        assert metrics.total_dimensions == snapshot.total_dimensions
        summary = CalibrationSummary.from_snapshot(snapshot)
        assert summary.overall_calibration_score == snapshot.overall_calibration_score

    def test_profile_validator_after_builder(self) -> None:
        profile = make_calibration_profile()
        result = CalibrationProfileValidator.validate(profile)
        assert result.is_valid, result.violations

    def test_statistics_from_built_profile(self) -> None:
        profile = make_calibration_profile()
        stats = CalibrationStatistics.from_profile(profile)
        assert stats.session_count_used == profile.session_count_used
        assert stats.total_feature_bands == len(profile.feature_bands)
