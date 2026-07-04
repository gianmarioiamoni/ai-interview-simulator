# domain/contracts/feature/__init__.py
# Feature Layer — Domain contracts (ADR-018, ADR-020, E01-M1, E01-M4)

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
# E01-M4 runtime support layer
from domain.contracts.feature.feature_batch import FeatureBatch
from domain.contracts.feature.feature_collection import FeatureCollection
from domain.contracts.feature.feature_statistics import FeatureStatistics
from domain.contracts.feature.feature_delta import DeltaDirection, FeatureDelta, FeatureDeltaSet
from domain.contracts.feature.feature_filter import FeatureFilter, FeaturePredicate
from domain.contracts.feature.feature_ordering import FeatureOrdering, FeatureSortKey
from domain.contracts.feature.feature_comparison import FeatureComparison, FeatureCollectionComparison

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
    # E01-M4
    "FeatureBatch",
    "FeatureCollection",
    "FeatureStatistics",
    "DeltaDirection",
    "FeatureDelta",
    "FeatureDeltaSet",
    "FeatureFilter",
    "FeaturePredicate",
    "FeatureOrdering",
    "FeatureSortKey",
    "FeatureComparison",
    "FeatureCollectionComparison",
]
