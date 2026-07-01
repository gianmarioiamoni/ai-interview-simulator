# services/interview_reasoner/profile/candidate_profile_factory.py
"""CandidateProfileFactory — constructs the final immutable CandidateProfile (M2-6C).

Receives individually updated field groups from the engine's updaters and
assembles the final frozen Pydantic object.  A dedicated factory keeps the
model_copy / constructor call in a single place.
"""

from __future__ import annotations

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.profile_dimension import ProfileDimension


class CandidateProfileFactory:
    """Assembles a new CandidateProfile from updated field groups."""

    def build(
        self,
        base: CandidateProfile,
        dimension_scores: dict[ProfileDimension, DimensionTrace] | None = None,
        questions_answered: int | None = None,
        areas_covered: list[str] | None = None,
        last_updated_at_question_index: int | None = None,
    ) -> CandidateProfile:
        """Merge updated fields into a new frozen CandidateProfile."""
        updates: dict = {}
        if dimension_scores is not None:
            updates["dimension_scores"] = dimension_scores
        if questions_answered is not None:
            updates["questions_answered"] = questions_answered
        if areas_covered is not None:
            updates["areas_covered"] = areas_covered
        if last_updated_at_question_index is not None:
            updates["last_updated_at_question_index"] = last_updated_at_question_index
        if not updates:
            return base
        return base.model_copy(update=updates)
