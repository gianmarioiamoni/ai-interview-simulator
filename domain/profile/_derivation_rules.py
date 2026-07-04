# domain/profile/_derivation_rules.py
# INTERNAL — do NOT import outside domain/profile/
# CandidateProfileDerivationRules — V1.2 frozen domain semantics (ADS-05, MIG-06 S-00)

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.reasoning.profile_dimension import ProfileDimension


# ---------------------------------------------------------------------------
# Internal support models
# ---------------------------------------------------------------------------


class FeatureDimensionMapping(BaseModel):
    """Single (FeatureType, ProfileDimension, weight) triple."""

    feature_type: FeatureType
    dimension: ProfileDimension
    weight: float = Field(..., gt=0.0, le=1.0)

    model_config = {"frozen": True, "extra": "forbid"}


class ValueProxyEntry(BaseModel):
    """Maps a feature value string to a numeric score in [0.0, 100.0].

    An empty value_string (or "*") is the fallback sentinel.
    """

    value_string: str
    numeric_score: float = Field(..., ge=0.0, le=100.0)

    model_config = {"frozen": True, "extra": "forbid"}


# ---------------------------------------------------------------------------
# Main rules object
# ---------------------------------------------------------------------------


class CandidateProfileDerivationRules(BaseModel):
    """Immutable domain rules object for CandidateProfile derivation (ADS-05).

    Contains ALL domain semantics: FeatureType mappings, contribution weights,
    value proxy table, thresholds. Contains NO mathematical algorithms.

    CandidateProfileDerivationService is the sole consumer.
    """

    rules_version: str = Field(..., min_length=1)

    # FeatureType → ProfileDimension mappings with weights.
    # CONFIDENCE and TREND have weight 0.0 and are NOT included here
    # (they act as modifiers, not score contributors).
    feature_dimension_map: tuple[FeatureDimensionMapping, ...] = Field(...)

    # Value string → numeric score. Exactly one fallback entry (value_string="*").
    value_proxy_table: tuple[ValueProxyEntry, ...] = Field(...)

    # Trend derivation thresholds (mirrors production TrendUpdater constants)
    min_evidence_for_trend: int = Field(..., ge=2)
    trend_threshold: float = Field(..., gt=0.0)

    # Confidence saturation (mirrors production DimensionTraceUpdater constants)
    max_evidence_confidence: int = Field(..., gt=0)
    low_confidence_max_evidence_modifier: int = Field(..., gt=0)

    # FeatureConfidence.is_low threshold (mirrors production FeatureConfidence)
    low_confidence_threshold: float = Field(..., ge=0.0, le=1.0)

    # areas_covered inclusion rules
    areas_covered_min_confidence: float = Field(..., ge=0.0, le=1.0)
    areas_covered_allow_nascent: bool = Field(...)

    # TREND feature override eligibility
    trend_override_eligible_features: frozenset[FeatureType] = Field(...)
    trend_override_max_delta: float = Field(..., gt=0.0)

    model_config = {"frozen": True, "extra": "forbid"}

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _validate_value_proxy_fallback(self) -> "CandidateProfileDerivationRules":
        """Exactly one fallback entry must exist (value_string == '*')."""
        fallbacks = [e for e in self.value_proxy_table if e.value_string == "*"]
        if len(fallbacks) != 1:
            raise ValueError(
                f"value_proxy_table must contain exactly one fallback entry "
                f"(value_string='*'); found {len(fallbacks)}"
            )
        return self

    @model_validator(mode="after")
    def _validate_low_confidence_modifier(self) -> "CandidateProfileDerivationRules":
        """low_confidence_max_evidence_modifier must be <= max_evidence_confidence."""
        if self.low_confidence_max_evidence_modifier > self.max_evidence_confidence:
            raise ValueError(
                f"low_confidence_max_evidence_modifier "
                f"({self.low_confidence_max_evidence_modifier}) must be "
                f"<= max_evidence_confidence ({self.max_evidence_confidence})"
            )
        return self

    # ------------------------------------------------------------------
    # Default factory
    # ------------------------------------------------------------------

    @classmethod
    def default(cls) -> "CandidateProfileDerivationRules":
        """Return the official V1.2 immutable rules instance."""
        return cls(
            rules_version="1.2.1",
            feature_dimension_map=(
                # TECHNICAL_SKILL → TECHNICAL_DEPTH (weight 1.0)
                FeatureDimensionMapping(
                    feature_type=FeatureType.TECHNICAL_SKILL,
                    dimension=ProfileDimension.TECHNICAL_DEPTH,
                    weight=1.0,
                ),
                # REASONING → PROBLEM_SOLVING (0.7), ENGINEERING_JUDGMENT (0.3)
                FeatureDimensionMapping(
                    feature_type=FeatureType.REASONING,
                    dimension=ProfileDimension.PROBLEM_SOLVING,
                    weight=0.7,
                ),
                FeatureDimensionMapping(
                    feature_type=FeatureType.REASONING,
                    dimension=ProfileDimension.ENGINEERING_JUDGMENT,
                    weight=0.3,
                ),
                # COMMUNICATION → COMMUNICATION (1.0)
                FeatureDimensionMapping(
                    feature_type=FeatureType.COMMUNICATION,
                    dimension=ProfileDimension.COMMUNICATION,
                    weight=1.0,
                ),
                # LEADERSHIP → ENGINEERING_JUDGMENT (0.5), PROBLEM_SOLVING (0.5)
                FeatureDimensionMapping(
                    feature_type=FeatureType.LEADERSHIP,
                    dimension=ProfileDimension.ENGINEERING_JUDGMENT,
                    weight=0.5,
                ),
                FeatureDimensionMapping(
                    feature_type=FeatureType.LEADERSHIP,
                    dimension=ProfileDimension.PROBLEM_SOLVING,
                    weight=0.5,
                ),
                # COLLABORATION → COMMUNICATION (0.5), ENGINEERING_JUDGMENT (0.5)
                FeatureDimensionMapping(
                    feature_type=FeatureType.COLLABORATION,
                    dimension=ProfileDimension.COMMUNICATION,
                    weight=0.5,
                ),
                FeatureDimensionMapping(
                    feature_type=FeatureType.COLLABORATION,
                    dimension=ProfileDimension.ENGINEERING_JUDGMENT,
                    weight=0.5,
                ),
                # ADAPTABILITY → PROBLEM_SOLVING (0.5), ENGINEERING_JUDGMENT (0.5)
                FeatureDimensionMapping(
                    feature_type=FeatureType.ADAPTABILITY,
                    dimension=ProfileDimension.PROBLEM_SOLVING,
                    weight=0.5,
                ),
                FeatureDimensionMapping(
                    feature_type=FeatureType.ADAPTABILITY,
                    dimension=ProfileDimension.ENGINEERING_JUDGMENT,
                    weight=0.5,
                ),
                # LEARNING → PROBLEM_SOLVING (0.4), TECHNICAL_DEPTH (0.6)
                FeatureDimensionMapping(
                    feature_type=FeatureType.LEARNING,
                    dimension=ProfileDimension.PROBLEM_SOLVING,
                    weight=0.4,
                ),
                FeatureDimensionMapping(
                    feature_type=FeatureType.LEARNING,
                    dimension=ProfileDimension.TECHNICAL_DEPTH,
                    weight=0.6,
                ),
                # LANGUAGE_CAPABILITY → COMMUNICATION (0.5)
                FeatureDimensionMapping(
                    feature_type=FeatureType.LANGUAGE_CAPABILITY,
                    dimension=ProfileDimension.COMMUNICATION,
                    weight=0.5,
                ),
                # TECHNICAL_SKILL → SYSTEM_DESIGN (0.5) — secondary signal (SR-02)
                FeatureDimensionMapping(
                    feature_type=FeatureType.TECHNICAL_SKILL,
                    dimension=ProfileDimension.SYSTEM_DESIGN,
                    weight=0.5,
                ),
                # REASONING → SYSTEM_DESIGN (0.4) — system design is reasoning-intensive (SR-02)
                FeatureDimensionMapping(
                    feature_type=FeatureType.REASONING,
                    dimension=ProfileDimension.SYSTEM_DESIGN,
                    weight=0.4,
                ),
            ),
            value_proxy_table=(
                ValueProxyEntry(value_string="HIGH", numeric_score=85.0),
                ValueProxyEntry(value_string="MODERATE_HIGH", numeric_score=70.0),
                ValueProxyEntry(value_string="MODERATE", numeric_score=55.0),
                ValueProxyEntry(value_string="MODERATE_LOW", numeric_score=40.0),
                ValueProxyEntry(value_string="LOW", numeric_score=20.0),
                ValueProxyEntry(value_string="*", numeric_score=50.0),
            ),
            min_evidence_for_trend=3,
            trend_threshold=8.0,
            max_evidence_confidence=10,
            low_confidence_max_evidence_modifier=8,
            low_confidence_threshold=0.3,
            areas_covered_min_confidence=0.3,
            areas_covered_allow_nascent=False,
            trend_override_eligible_features=frozenset({FeatureType.TREND}),
            trend_override_max_delta=8.0,
        )
