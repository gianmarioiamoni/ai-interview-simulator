# domain/profile/candidate_profile_builder.py
"""CandidateProfileBuilder — sole creator of CandidateProfile in the domain layer.

Constraints (ADR-037, ADR-032):
- Builder is the ONLY permitted constructor path for CandidateProfile.
- No persistence, no SessionHistory, no Replay, no Narrative, no Coaching.
- Produces immutable frozen objects only.
- Fluent interface; each with_* method returns self for chaining.
"""

from __future__ import annotations

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.profile_signal import ProfileSignal
from domain.contracts.reasoning.signal_trace import SignalTrace


class CandidateProfileBuilder:
    """Builds an immutable CandidateProfile.

    Usage::

        profile = (
            CandidateProfileBuilder()
            .with_dimension(ProfileDimension.TECHNICAL_DEPTH, trace)
            .with_questions_answered(3)
            .with_areas_covered(["algorithms", "system design"])
            .with_last_updated_at(2)
            .build()
        )
    """

    def __init__(self) -> None:
        self._dimension_scores: dict[ProfileDimension, DimensionTrace] = {}
        self._signals: dict[ProfileSignal, SignalTrace] = {}
        self._questions_answered: int = 0
        self._areas_covered: list[str] = []
        self._last_updated_at_question_index: int = -1

    # ------------------------------------------------------------------
    # Fluent setters
    # ------------------------------------------------------------------

    def with_dimension(
        self,
        dimension: ProfileDimension,
        trace: DimensionTrace,
    ) -> "CandidateProfileBuilder":
        self._dimension_scores[dimension] = trace
        return self

    def with_dimensions(
        self,
        dimension_scores: dict[ProfileDimension, DimensionTrace],
    ) -> "CandidateProfileBuilder":
        self._dimension_scores = dict(dimension_scores)
        return self

    def with_signal(
        self,
        signal: ProfileSignal,
        trace: SignalTrace,
    ) -> "CandidateProfileBuilder":
        self._signals[signal] = trace
        return self

    def with_signals(
        self,
        signals: dict[ProfileSignal, SignalTrace],
    ) -> "CandidateProfileBuilder":
        self._signals = dict(signals)
        return self

    def with_questions_answered(self, count: int) -> "CandidateProfileBuilder":
        if count < 0:
            raise ValueError(f"questions_answered must be >= 0, got {count}")
        self._questions_answered = count
        return self

    def with_areas_covered(self, areas: list[str]) -> "CandidateProfileBuilder":
        self._areas_covered = list(areas)
        return self

    def with_last_updated_at(self, question_index: int) -> "CandidateProfileBuilder":
        self._last_updated_at_question_index = question_index
        return self

    # ------------------------------------------------------------------
    # Derivation from an existing profile (copy-and-update)
    # ------------------------------------------------------------------

    @classmethod
    def from_profile(cls, profile: CandidateProfile) -> "CandidateProfileBuilder":
        """Seed a new builder with the state of an existing profile."""
        builder = cls()
        builder._dimension_scores = dict(profile.dimension_scores)
        builder._signals = dict(profile.signals)
        builder._questions_answered = profile.questions_answered
        builder._areas_covered = list(profile.areas_covered)
        builder._last_updated_at_question_index = profile.last_updated_at_question_index
        return builder

    # ------------------------------------------------------------------
    # Terminal
    # ------------------------------------------------------------------

    def build(self) -> CandidateProfile:
        """Produce an immutable CandidateProfile. Sole creation path."""
        return CandidateProfile(
            dimension_scores=self._dimension_scores,
            signals=self._signals,
            questions_answered=self._questions_answered,
            areas_covered=self._areas_covered,
            last_updated_at_question_index=self._last_updated_at_question_index,
        )
