# domain/contracts/feature/feature_merge_policy.py
# FeatureMergePolicy interface — combines compatible candidates (ADR-020 §C, §I)

from abc import ABC, abstractmethod

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.profile_feature import ProfileFeature


class FeatureMergePolicy(ABC):
    """Combines directionally compatible FeatureCandidates into a single ProfileFeature.

    Invoked by FeatureComposer when two or more candidates for the same FeatureIdentity
    are directionally compatible (e.g., both HIGH, or one HIGH and one MODERATE).

    Merge semantics (ADR-020 §C):
    - Confidence: weighted average of candidate confidences, weighted by Observation count.
    - Value: higher-confidence candidate takes precedence for directional value.
    - Provenance: union of both candidates' source_observation_ids.
    - Stability: derived from the merged result's consistency across cycles.

    When candidates are contradictory, FeatureReplacementPolicy is used instead.
    """

    @abstractmethod
    def merge(
        self,
        candidates: list[FeatureCandidate],
        candidate_identity_id: str,
        feature_engine_version: str,
    ) -> ProfileFeature:
        """Merge compatible candidates into one ProfileFeature.

        Args:
            candidates: Two or more compatible FeatureCandidates for the same FeatureIdentity.
            candidate_identity_id: Owning candidate identifier.
            feature_engine_version: FeatureEngine version for provenance.

        Returns:
            A single ProfileFeature representing the merged knowledge.

        Raises:
            ValueError: if candidates is empty or candidates span multiple FeatureIdentities.
        """

    @abstractmethod
    def are_compatible(self, a: FeatureCandidate, b: FeatureCandidate) -> bool:
        """Return True if a and b can be merged (not contradictory).

        Contradictory candidates (e.g., HIGH vs LOW with equal confidence) must be
        routed to FeatureReplacementPolicy instead.
        """
