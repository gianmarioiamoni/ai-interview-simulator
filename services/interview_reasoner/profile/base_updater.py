# services/interview_reasoner/profile/base_updater.py
"""Abstract ProfileUpdater contract (M2-6C).

Each concrete updater is responsible for ONE aspect of CandidateProfile evolution.
All implementations must be:
  - Stateless
  - Deterministic
  - O(n) in the number of new signals
  - Side-effect-free (return new profile, never mutate)
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.evidence_signal import EvidenceSignal


class ProfileUpdater(ABC):
    """Contract for a single focused profile update operation.

    Implementors receive the current (immutable) profile and the list of
    new evidence signals produced in the current reasoning cycle, and
    return a new (immutable) profile with one aspect updated.
    """

    @abstractmethod
    def update(
        self,
        profile: CandidateProfile,
        new_signals: list[EvidenceSignal],
        question_index: int,
    ) -> CandidateProfile:
        """Return an updated profile.  Must never mutate ``profile``."""
