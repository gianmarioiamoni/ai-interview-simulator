# services/interview_reasoner/profile/coverage_updater.py
"""CoverageUpdater — updates questions_answered and areas_covered (M2-6C).

Responsibilities:
- Increment questions_answered when question_index is new (not previously recorded).
- Append new question_areas that are not already in areas_covered.

The updater receives the profile AFTER DimensionTraceUpdater has already stamped
last_updated_at_question_index. To determine whether this is a new question it
receives `prev_last_updated` explicitly from the engine — the last_updated value
before this cycle's updates.

Fully deterministic. O(k) in new signals.
"""

from __future__ import annotations

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from services.interview_reasoner.profile.base_updater import ProfileUpdater


class CoverageUpdater(ProfileUpdater):
    """Updates questions_answered and areas_covered from new evidence signals."""

    def update(
        self,
        profile: CandidateProfile,
        new_signals: list[EvidenceSignal],
        question_index: int,
        prev_last_updated: int = -1,
    ) -> CandidateProfile:
        """Update coverage fields.

        Args:
            profile: the profile to update (may already have updated dimension_scores).
            new_signals: signals produced in this cycle.
            question_index: current question index.
            prev_last_updated: the last_updated_at_question_index value BEFORE this
                cycle's DimensionTraceUpdater ran. Used to detect new questions.
        """
        if not new_signals:
            return profile

        # Areas covered: accumulate unique non-empty areas
        existing_areas = set(profile.areas_covered)
        seen: set[str] = set()
        unique_new_areas: list[str] = []
        for sig in new_signals:
            if sig.question_area and sig.question_area not in existing_areas and sig.question_area not in seen:
                seen.add(sig.question_area)
                unique_new_areas.append(sig.question_area)

        # questions_answered: increment only if this is a genuinely new question.
        questions_answered = profile.questions_answered
        if question_index > prev_last_updated:
            questions_answered += 1

        if not unique_new_areas and questions_answered == profile.questions_answered:
            return profile

        return profile.model_copy(update={
            "questions_answered": questions_answered,
            "areas_covered": profile.areas_covered + unique_new_areas,
        })
