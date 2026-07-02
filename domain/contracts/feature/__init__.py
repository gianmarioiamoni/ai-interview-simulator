# domain/contracts/feature/__init__.py
# Feature Layer — Domain contracts (ADR-018, ADR-020, E01-M1)

from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_quality import (
    STABILITY_STABLE,
    STABILITY_UNSTABLE,
    STABILITY_EMERGING,
    MATURITY_NASCENT,
    MATURITY_DEVELOPING,
    MATURITY_MATURE,
    FeatureConfidence,
    FeatureStability,
    FeatureMaturity,
    FeatureQuality,
)
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.feature.feature_composer import FeatureComposer
from domain.contracts.feature.feature_updater import FeatureUpdater
from domain.contracts.feature.feature_merge_policy import FeatureMergePolicy
from domain.contracts.feature.feature_replacement_policy import FeatureReplacementPolicy

__all__ = [
    "STABILITY_STABLE",
    "STABILITY_UNSTABLE",
    "STABILITY_EMERGING",
    "MATURITY_NASCENT",
    "MATURITY_DEVELOPING",
    "MATURITY_MATURE",
    "FeatureType",
    "FeatureIdentity",
    "FeatureConfidence",
    "FeatureStability",
    "FeatureMaturity",
    "FeatureQuality",
    "FeatureProvenance",
    "FeatureCandidate",
    "ProfileFeature",
    "FeatureComposer",
    "FeatureUpdater",
    "FeatureMergePolicy",
    "FeatureReplacementPolicy",
]
