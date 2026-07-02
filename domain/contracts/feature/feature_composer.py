# domain/contracts/feature/feature_composer.py
# FeatureComposer interface — resolves FeatureCandidates into ProfileFeatures (ADR-020 §C)

from abc import ABC, abstractmethod

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.profile_feature import ProfileFeature


class FeatureComposer(ABC):
    """Resolves all FeatureCandidates from all Updaters into a ProfileFeature set.

    Contract (ADR-020 §C):
    - Receives the full FeatureCandidate[] from all Updaters for one cycle.
    - Applies FeatureMergePolicy (compatible candidates) or FeatureReplacementPolicy
      (contradictory candidates) to produce exactly one ProfileFeature per FeatureIdentity.
    - Assigns final quality metadata: confidence, stability, maturity.
    - Stateless per invocation — no state retained between calls.
    - Never writes to any aggregate directly.

    Invariant: every FeatureIdentity present in candidates must appear exactly once
    in the returned ProfileFeature list.
    """

    @abstractmethod
    def compose(
        self,
        candidates: list[FeatureCandidate],
        candidate_identity_id: str,
        feature_engine_version: str,
    ) -> list[ProfileFeature]:
        """Compose candidates into the final ProfileFeature set for one cycle.

        Args:
            candidates: All FeatureCandidates collected from all Updaters this cycle.
            candidate_identity_id: Owning candidate identifier (ADR-016A).
            feature_engine_version: FeatureEngine version string for provenance.

        Returns:
            One ProfileFeature per distinct FeatureIdentity, with resolved quality
            metadata and complete provenance.
        """
