# domain/contracts/calibration/calibration_statistics.py
# EPIC-06 E06-M1 — CalibrationStatistics (aggregate metrics over CalibrationProfile)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.calibration.calibration_profile import CalibrationProfile


class CalibrationStatistics(BaseModel):
    """Aggregate metrics derived from a CalibrationProfile.

    Pure computation — no LLM, no business logic, no mutation.
    Mirrors KnowledgeSnapshotStatistics / LearningProgressStatistics patterns.
    """

    candidate_identity_id: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    seniority: str = Field(..., min_length=1)

    total_feature_bands: int = Field(..., ge=0)
    session_count_used: int = Field(..., ge=0)
    unique_feature_type_ids: frozenset[str] = Field(default_factory=frozenset)

    mean_expected_min: float = Field(default=0.0, ge=0.0, le=1.0)
    mean_expected_max: float = Field(default=0.0, ge=0.0, le=1.0)
    mean_expected_mean: float = Field(default=0.0, ge=0.0, le=1.0)
    mean_band_width: float = Field(
        default=0.0, ge=0.0, description="Mean of (expected_max - expected_min) per band"
    )

    knowledge_epoch: str = Field(..., min_length=1)
    is_empty: bool = Field(default=False)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_profile(cls, profile: CalibrationProfile) -> "CalibrationStatistics":
        """Compute statistics from a CalibrationProfile. Pure derivation."""
        bands = profile.feature_bands
        if not bands:
            return cls(
                candidate_identity_id=profile.candidate_identity_id,
                role=profile.role,
                seniority=profile.seniority,
                total_feature_bands=0,
                session_count_used=profile.session_count_used,
                knowledge_epoch=profile.knowledge_epoch,
                is_empty=True,
            )

        n = len(bands)
        mean_min = sum(b.expected_min for b in bands) / n
        mean_max = sum(b.expected_max for b in bands) / n
        mean_mean = sum(b.expected_mean for b in bands) / n
        mean_width = sum(b.expected_max - b.expected_min for b in bands) / n

        return cls(
            candidate_identity_id=profile.candidate_identity_id,
            role=profile.role,
            seniority=profile.seniority,
            total_feature_bands=n,
            session_count_used=profile.session_count_used,
            unique_feature_type_ids=profile.feature_type_ids,
            mean_expected_min=mean_min,
            mean_expected_max=mean_max,
            mean_expected_mean=mean_mean,
            mean_band_width=mean_width,
            knowledge_epoch=profile.knowledge_epoch,
            is_empty=False,
        )
