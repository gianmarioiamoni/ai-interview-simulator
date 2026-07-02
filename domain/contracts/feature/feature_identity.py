# domain/contracts/feature/feature_identity.py
# FeatureIdentity — stable cross-session identity (ADR-020 §F)

from pydantic import BaseModel, Field

from domain.contracts.feature.feature_type import FeatureType


class FeatureIdentity(BaseModel):
    """Semantic identity of a ProfileFeature across schema versions, cycles, and sessions.

    Identity = (feature_type_id, semantic_category).
    schema_version qualifies the representation; it is NOT part of identity.

    Invariant (ADR-020 §F): schema evolution must never change FeatureIdentity.
    All FeatureIdentity values are registered statically; none may be created at runtime.
    """

    feature_type_id: str = Field(
        ..., min_length=1, description="Stable string key; never changes across schema versions"
    )
    semantic_category: str = Field(
        ..., min_length=1, description="Conceptual dimension (e.g. 'analytical_reasoning')"
    )
    schema_version: str = Field(default="1.0", description="Feature schema version at registration")

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def for_type(cls, feature_type: FeatureType) -> "FeatureIdentity":
        """Factory — returns the canonical FeatureIdentity for a V1.2 taxonomy type."""
        return _IDENTITY_REGISTRY[feature_type]


# V1.2 canonical registry — one entry per FeatureType (ADR-020 §F)
_IDENTITY_REGISTRY: dict[FeatureType, "FeatureIdentity"] = {
    FeatureType.TECHNICAL_SKILL: FeatureIdentity(
        feature_type_id="technical_skill_feature",
        semantic_category="technical_knowledge",
    ),
    FeatureType.REASONING: FeatureIdentity(
        feature_type_id="reasoning_feature",
        semantic_category="analytical_reasoning",
    ),
    FeatureType.COMMUNICATION: FeatureIdentity(
        feature_type_id="communication_feature",
        semantic_category="communication_clarity",
    ),
    FeatureType.LEADERSHIP: FeatureIdentity(
        feature_type_id="leadership_feature",
        semantic_category="leadership_behaviour",
    ),
    FeatureType.COLLABORATION: FeatureIdentity(
        feature_type_id="collaboration_feature",
        semantic_category="collaboration_behaviour",
    ),
    FeatureType.ADAPTABILITY: FeatureIdentity(
        feature_type_id="adaptability_feature",
        semantic_category="adaptability_capacity",
    ),
    FeatureType.LEARNING: FeatureIdentity(
        feature_type_id="learning_feature",
        semantic_category="in_session_learning",
    ),
    FeatureType.CONFIDENCE: FeatureIdentity(
        feature_type_id="confidence_feature",
        semantic_category="confidence_calibration",
    ),
    FeatureType.LANGUAGE_CAPABILITY: FeatureIdentity(
        feature_type_id="language_capability_feature",
        semantic_category="language_idiomatic_proficiency",
    ),
    FeatureType.COVERAGE: FeatureIdentity(
        feature_type_id="coverage_feature",
        semantic_category="topic_coverage_breadth",
    ),
    FeatureType.TREND: FeatureIdentity(
        feature_type_id="trend_feature",
        semantic_category="performance_trend_direction",
    ),
}
