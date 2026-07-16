# app/ui/views/report/learning_progress_binder.py
# EPIC-V13-05 Phase 5 — bind persisted LongitudinalProfile → LearningProgress at report UI time.

from __future__ import annotations

from pathlib import Path

from domain.contracts.longitudinal.longitudinal_profile_repository import (
    LongitudinalProfileRepository,
)
from domain.contracts.progress.learning_progress import LearningProgress
from services.progress.progress_tracker import ProgressTracker

_DEFAULT_LONGITUDINAL_STORAGE = Path("data/longitudinal")


def bind_learning_progress(
    candidate_identity_id: str,
    *,
    progress_tracker: ProgressTracker | None = None,
    repository: LongitudinalProfileRepository | None = None,
) -> LearningProgress:
    """Load LearningProgress for report presentation from persisted LongitudinalProfile.

    Uses Report.candidate_identity_id as the bind key (Data Model §2.6).
    Does not read SessionHistory. Does not write domain artifacts.
    Empty / absent profile yields empty LearningProgress (insufficient-data UI).
    """
    if not candidate_identity_id or not candidate_identity_id.strip():
        raise ValueError(
            "candidate_identity_id is required to bind LearningProgress for report presentation"
        )

    tracker = progress_tracker or _default_progress_tracker(repository=repository)
    return tracker.get_progress(candidate_identity_id)


def _default_progress_tracker(
    *,
    repository: LongitudinalProfileRepository | None = None,
) -> ProgressTracker:
    if repository is None:
        from infrastructure.longitudinal.longitudinal_profile_repository_impl import (
            JsonFileLongitudinalProfileRepository,
        )

        repository = JsonFileLongitudinalProfileRepository(
            storage_dir=_DEFAULT_LONGITUDINAL_STORAGE
        )
    return ProgressTracker(repository=repository)
