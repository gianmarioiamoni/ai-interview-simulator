# services/interview_reasoner/profile/dominant_dimension_calculator.py
"""DominantDimensionCalculator — session-scoped dominant dimension (M2-6C).

Unlike the per-cycle calculation in ReasonerService, this operates on the
full DimensionTrace map (i.e., accumulated across the whole session).

Criteria (priority):
  1. Highest evidence_count (most observed dimension).
  2. Tie-break: lowest average_score (most problematic dimension deserves focus).

Returns None when the profile has no dimension traces.
"""

from __future__ import annotations

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.profile_dimension import ProfileDimension


class DominantDimensionCalculator:
    """Computes the session-scoped dominant dimension from DimensionTrace map."""

    def calculate(
        self,
        profile: CandidateProfile,
    ) -> ProfileDimension | None:
        if not profile.dimension_scores:
            return None
        return max(
            profile.dimension_scores,
            key=lambda dim: (
                profile.dimension_scores[dim].evidence_count,
                -profile.dimension_scores[dim].average_score,
            ),
        )
