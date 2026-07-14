# domain/contracts/longitudinal/longitudinal_profile_repository.py
# EPIC-02 — P1/C3 — LongitudinalProfileRepository interface (domain layer)
# Governing: ADR-034 Decision 8, EPIC-02-DATA-MODEL.md §4.2
# Concrete implementation is infrastructure layer scope (P3/C1).

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from domain.contracts.longitudinal.longitudinal_profile import LongitudinalProfile


class LongitudinalProfileRepository(ABC):
    """Abstract repository interface for LongitudinalProfile persistence (ADR-034 Decision 8).

    Declared in the domain layer. Concrete adapter lives in the infrastructure layer (P3/C1).

    Query model (EPIC-02-DATA-MODEL.md §4.2):
    - get(candidate_identity_id) → Optional[LongitudinalProfile]
    - save(profile) → None  (replace-on-write; idempotent for same candidate_identity_id)
    - exists(candidate_identity_id) → bool

    No batch operations, no pagination, no list queries in V1.3.
    """

    @abstractmethod
    def get(self, candidate_identity_id: str) -> Optional[LongitudinalProfile]:
        """Return the current LongitudinalProfile for the given candidate, or None."""

    @abstractmethod
    def save(self, profile: LongitudinalProfile) -> None:
        """Persist the profile using replace-on-write semantics.

        If a profile already exists for profile.candidate_identity_id,
        it is replaced atomically. Idempotent for identical payloads.
        """

    @abstractmethod
    def exists(self, candidate_identity_id: str) -> bool:
        """Return True if a profile exists for the given candidate, False otherwise."""
