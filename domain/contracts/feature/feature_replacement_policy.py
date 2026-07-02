# domain/contracts/feature/feature_replacement_policy.py
# FeatureReplacementPolicy interface — selects winner among contradictory candidates (ADR-020 §C, §I)

from abc import ABC, abstractmethod

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.profile_feature import ProfileFeature


class FeatureReplacementPolicy(ABC):
    """Selects one candidate and discards others when candidates are contradictory.

    Invoked by FeatureComposer when FeatureMergePolicy reports candidates are not
    compatible (e.g., TechnicalSkillFeature HIGH vs LOW with equal confidence).

    Replacement semantics (ADR-020 §C, §I):
    - Winner: candidate with the higher Observation count.
    - Tie-break: candidate produced from more recent Observations
      (higher computed_at_question_index).
    - Discarded candidates: their source_observation_ids are recorded in
      provenance.superseded_observation_ids — never lost.
    """

    @abstractmethod
    def replace(
        self,
        candidates: list[FeatureCandidate],
        candidate_identity_id: str,
        feature_engine_version: str,
    ) -> ProfileFeature:
        """Select the winning candidate and produce a ProfileFeature.

        Args:
            candidates: Two or more contradictory FeatureCandidates for the same FeatureIdentity.
            candidate_identity_id: Owning candidate identifier.
            feature_engine_version: FeatureEngine version for provenance.

        Returns:
            A single ProfileFeature representing the winning candidate.
            Discarded candidates' provenance is captured in superseded_observation_ids.

        Raises:
            ValueError: if candidates is empty or spans multiple FeatureIdentities.
        """

    @abstractmethod
    def select_winner(
        self, a: FeatureCandidate, b: FeatureCandidate
    ) -> FeatureCandidate:
        """Return the winning candidate between two contradictory candidates.

        Tie-breaking rule (ADR-020 §I):
        1. Higher len(source_observation_ids) wins.
        2. Tie-break: higher computed_at_question_index wins.
        """
