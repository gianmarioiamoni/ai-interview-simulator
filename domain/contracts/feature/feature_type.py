# domain/contracts/feature/feature_type.py
# Feature taxonomy — V1.2 frozen (ADR-018 §D)

from enum import Enum


class FeatureType(str, Enum):
    """V1.2 frozen ProfileFeature taxonomy (ADR-018 §D).

    Invariant: no type name may reference a programming language.
    All 11 types are language-independent. Extension requires a new ADR.
    """

    TECHNICAL_SKILL = "technical_skill_feature"
    REASONING = "reasoning_feature"
    COMMUNICATION = "communication_feature"
    LEADERSHIP = "leadership_feature"
    COLLABORATION = "collaboration_feature"
    ADAPTABILITY = "adaptability_feature"
    LEARNING = "learning_feature"
    CONFIDENCE = "confidence_feature"
    LANGUAGE_CAPABILITY = "language_capability_feature"
    COVERAGE = "coverage_feature"
    TREND = "trend_feature"
