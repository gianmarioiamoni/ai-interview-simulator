# tests/domain/profile/profile_test_helpers.py
"""Test-only helpers for CandidateProfile consumers that need DimensionTrace fixtures.

Production code must build profiles via CandidateProfileBuilder with features.
These helpers inject a derived-projection cache for unit tests of statistics,
comparison, delta, and detector modules that exercise DimensionTrace semantics
without constructing a full FeatureEngine feature set.
"""

from __future__ import annotations

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.profile_signal import ProfileSignal
from domain.contracts.reasoning.signal_trace import SignalTrace


def candidate_profile_with_dimension_scores(
    dimension_scores: dict[ProfileDimension, DimensionTrace],
    *,
    questions_answered: int = 0,
    areas_covered: list[str] | None = None,
    last_updated_at_question_index: int = -1,
    signals: dict[ProfileSignal, SignalTrace] | None = None,
) -> CandidateProfile:
    """Return a CandidateProfile whose dimension_scores projection matches *dimension_scores*."""
    profile = CandidateProfile(
        questions_answered=questions_answered,
        areas_covered=list(areas_covered or []),
        last_updated_at_question_index=last_updated_at_question_index,
        signals=dict(signals or {}),
    )
    object.__setattr__(profile, "_derived_dimension_scores", dict(dimension_scores))
    return profile
