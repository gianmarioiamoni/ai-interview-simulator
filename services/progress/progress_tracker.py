# services/progress/progress_tracker.py
# EPIC-02/P5-C1 — ProgressTracker service
#
# Governing: ADR-034 Decision 1 (declared reader of LongitudinalProfile),
#            ADR-034 Decision 5 (LearningProgress derived from LongitudinalProfile only),
#            EPIC-02-IMPLEMENTATION-PLAN.md §5 (P5-C1 scope).
#
# Responsibilities:
#   - Read LongitudinalProfile from repository for a given candidate.
#   - Delegate LearningProgress construction to LearningProgressBuilder.
#   - Return LearningProgress with behavioral trend data when 2+ sessions present.
#   - Return LearningProgress with has_sufficient_data=False when 0 or 1 session present.
#
# Invariants preserved:
#   - No SessionHistory[] consumed directly (SR-06 / ADR-034 Decision 5).
#   - No LLM calls, no FeatureEngine, no NarrativeGenerator (LP-03).
#   - No write to LongitudinalProfile (sole writer is longitudinal_update_node — LP-01).
#   - No persistence of LearningProgress (LP-LP-06).

from __future__ import annotations

from typing import Optional

from domain.contracts.longitudinal.longitudinal_profile_repository import (
    LongitudinalProfileRepository,
)
from domain.contracts.progress.learning_progress import LearningProgress
from domain.contracts.progress.learning_progress_builder import LearningProgressBuilder
from app.core.logger import get_logger

logger = get_logger(__name__)


class ProgressTracker:
    """Service that derives LearningProgress from a persisted LongitudinalProfile.

    Read-only with respect to LongitudinalProfile. Delegates all derivation logic
    to LearningProgressBuilder (LP-LP-07).

    Not responsible for LongitudinalProfile accumulation — that is the sole
    responsibility of longitudinal_update_node (ADR-034 Decision 1, LP-01).

    Usage::

        tracker = ProgressTracker(repository)
        progress = tracker.get_progress(candidate_identity_id)
    """

    def __init__(self, repository: LongitudinalProfileRepository) -> None:
        self._repository = repository

    def get_progress(
        self,
        candidate_identity_id: str,
        *,
        schema_version: str = "1.0",
        metadata: Optional[dict[str, str]] = None,
    ) -> LearningProgress:
        """Derive LearningProgress for the given candidate.

        Reads LongitudinalProfile from the repository. If no profile exists
        (first-session candidate or pre-first-session state), returns a
        LearningProgress with has_sufficient_data=False and empty entries.

        Args:
            candidate_identity_id: The candidate's identity identifier.
            schema_version: Schema version string for the produced LearningProgress.
            metadata: Optional key-value metadata to embed in LearningProgress.

        Returns:
            LearningProgress derived from the candidate's LongitudinalProfile.
            has_sufficient_data is True iff session_count >= 2.
        """
        profile = self._repository.get(candidate_identity_id)

        if profile is None:
            logger.debug(
                "ProgressTracker: no LongitudinalProfile found for candidate=%s "
                "— returning empty LearningProgress",
                candidate_identity_id,
            )

        return (
            LearningProgressBuilder()
            .with_candidate_identity_id(candidate_identity_id)
            .with_longitudinal_profile(profile)
            .with_schema_version(schema_version)
            .with_metadata(metadata or {})
            .build()
        )
