# domain/profile/_derived_profile_data.py
# INTERNAL — do NOT import outside domain/profile/
# Transfer object from CandidateProfileDerivationService → CandidateProfileBuilder
# (ADS-04, ADS-05, MIG-06 P0)

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.profile_dimension import ProfileDimension


class DerivedProfileData(BaseModel):
    """Internal immutable transfer object produced by CandidateProfileDerivationService.

    Carries all computed values required by CandidateProfileBuilder.with_derived_data().
    Contains NO domain logic and NO algorithms — pure data carrier (ADS-04, PAT-08).

    Sole producer: CandidateProfileDerivationService (S-02, not yet implemented).
    Sole consumer: CandidateProfileBuilder.with_derived_data() (S-03, not yet implemented).
    """

    # Scored dimensions — only dimensions with >= 1 contributing feature are present.
    # Keys absent from this dict mean zero features mapped to that dimension.
    dimension_scores: dict[ProfileDimension, DimensionTrace] = Field(
        default_factory=dict,
        description=(
            "ProfileDimension → DimensionTrace for every dimension "
            "with at least one contributing feature."
        ),
    )

    # Unique question positions that produced at least one feature.
    questions_answered: int = Field(
        ...,
        ge=0,
        description="Count of unique computed_at_question_index values across all features.",
    )

    # Concept-level areas seen — sorted, deduplicated, filtered by maturity/confidence.
    areas_covered: list[str] = Field(
        default_factory=list,
        description="Sorted unique semantic_category values passing maturity/confidence filter.",
    )

    # len(scored_dims_with_evidence) / len(ProfileDimension), rounded to 4 dp.
    coverage_ratio: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fraction of ProfileDimensions with evidence_count >= 1, in [0.0, 1.0].",
    )

    # argmax by evidence_count desc, then average_score asc; None when dimension_scores empty.
    dominant_dimension: ProfileDimension | None = Field(
        default=None,
        description="Dimension with most evidence; lowest score wins ties.",
    )

    # argmin by average_score asc, then evidence_count desc; None when dimension_scores empty.
    weakest_dimension: ProfileDimension | None = Field(
        default=None,
        description="Dimension with lowest average score; most evidence wins ties.",
    )

    # Source features passed through verbatim — preserved for CandidateProfile.features.
    source_features: tuple[ProfileFeature, ...] = Field(
        default_factory=tuple,
        description="ProfileFeature tuple passed to DerivationService; stored verbatim.",
    )

    # Index of the most recently computed feature across all source features; -1 if empty.
    last_updated_at_question_index: int = Field(
        default=-1,
        description="max(computed_at_question_index) over source_features, or -1.",
    )

    model_config = {"frozen": True, "extra": "forbid"}

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _validate_dominant_in_scores(self) -> "DerivedProfileData":
        if self.dominant_dimension is not None:
            if self.dominant_dimension not in self.dimension_scores:
                raise ValueError(
                    f"dominant_dimension {self.dominant_dimension!r} "
                    "is not present in dimension_scores"
                )
        return self

    @model_validator(mode="after")
    def _validate_weakest_in_scores(self) -> "DerivedProfileData":
        if self.weakest_dimension is not None:
            if self.weakest_dimension not in self.dimension_scores:
                raise ValueError(
                    f"weakest_dimension {self.weakest_dimension!r} "
                    "is not present in dimension_scores"
                )
        return self

    @model_validator(mode="after")
    def _validate_dominant_weakest_distinct(self) -> "DerivedProfileData":
        if (
            self.dominant_dimension is not None
            and self.weakest_dimension is not None
            and len(self.dimension_scores) > 1
            and self.dominant_dimension == self.weakest_dimension
        ):
            raise ValueError(
                "dominant_dimension and weakest_dimension must differ "
                "when more than one dimension has evidence"
            )
        return self

    @model_validator(mode="after")
    def _validate_coverage_ratio_range(self) -> "DerivedProfileData":
        scored = sum(
            1
            for trace in self.dimension_scores.values()
            if trace.evidence_count >= 1
        )
        total = len(ProfileDimension)
        expected = round(scored / total, 4) if total > 0 else 0.0
        if abs(self.coverage_ratio - expected) > 1e-4:
            raise ValueError(
                f"coverage_ratio {self.coverage_ratio} does not match "
                f"computed value {expected} "
                f"(scored_dims={scored}, total_dims={total})"
            )
        return self

    @model_validator(mode="after")
    def _validate_last_updated_at_question_index(self) -> "DerivedProfileData":
        if not self.source_features:
            if self.last_updated_at_question_index != -1:
                raise ValueError(
                    "last_updated_at_question_index must be -1 when source_features is empty"
                )
        else:
            expected = max(
                f.computed_at_question_index for f in self.source_features
            )
            if self.last_updated_at_question_index != expected:
                raise ValueError(
                    f"last_updated_at_question_index {self.last_updated_at_question_index} "
                    f"does not match max(computed_at_question_index)={expected}"
                )
        return self

    @model_validator(mode="after")
    def _validate_areas_covered_sorted(self) -> "DerivedProfileData":
        if self.areas_covered != sorted(self.areas_covered):
            raise ValueError("areas_covered must be sorted")
        return self

    @model_validator(mode="after")
    def _validate_areas_covered_unique(self) -> "DerivedProfileData":
        if len(self.areas_covered) != len(set(self.areas_covered)):
            raise ValueError("areas_covered must contain unique values")
        return self
