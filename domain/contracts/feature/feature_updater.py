# domain/contracts/feature/feature_updater.py
# FeatureUpdater interface — produces FeatureCandidates from Observations (ADR-020 §C, §D)

from abc import ABC, abstractmethod
from typing import Any

from domain.contracts.feature.feature_candidate import FeatureCandidate


class FeatureUpdater(ABC):
    """Reads a subset of Observations and produces FeatureCandidate[].

    Contract (ADR-020 §C, §D):
    - Each Updater handles a defined subset of ObservationType values.
    - Updaters are independent — they do not read each other's candidates.
    - Stateless per invocation — receives full Observation[] and produces candidates
      without retaining state between calls.
    - Never modifies Observations.
    - Never writes to any aggregate.
    - Produces FeatureCandidates only — commits are FeatureEngine's responsibility.

    Registration (ADR-020 §J):
    - updater_id: stable identifier; must be unique in UpdaterRegistry.
    - observation_type_set: the set of ObservationType values this Updater handles.
    - feature_identity_set: the set of FeatureIdentity values this Updater may produce.
    - invocation_order: deterministic invocation position within FeatureEngine.
    """

    @property
    @abstractmethod
    def updater_id(self) -> str:
        """Stable identifier for this Updater (used in provenance and UpdaterRegistry)."""

    @property
    @abstractmethod
    def observation_type_set(self) -> frozenset[str]:
        """ObservationType values this Updater consumes."""

    @property
    @abstractmethod
    def feature_identity_set(self) -> frozenset[str]:
        """feature_type_id values this Updater may produce."""

    @property
    @abstractmethod
    def invocation_order(self) -> int:
        """Deterministic position within FeatureEngine's Updater sequence."""

    @abstractmethod
    def produce(self, observations: list[Any]) -> list[FeatureCandidate]:
        """Produce FeatureCandidates from the given Observations.

        Args:
            observations: Freshness-filtered, question_index-ordered Observations
                          from ObservationStore for this cycle.

        Returns:
            FeatureCandidate list — may be empty if no relevant Observations were found.
        """
