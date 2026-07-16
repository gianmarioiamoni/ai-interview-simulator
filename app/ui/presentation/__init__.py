# app/ui/presentation/__init__.py
# EPIC-07 P1/C1 — presentation-plane primitives (UI-layer; non-persistent).

from app.ui.presentation.async_boundary import AsyncBoundary
from app.ui.presentation.candidate_facing_error import CandidateFacingError
from app.ui.presentation.candidate_facing_error_catalog import (
    CANDIDATE_FACING_ERROR_CATALOG,
    CandidateFacingErrorCatalogEntry,
    get_candidate_facing_error_entry,
)

__all__ = [
    "AsyncBoundary",
    "CandidateFacingError",
    "CANDIDATE_FACING_ERROR_CATALOG",
    "CandidateFacingErrorCatalogEntry",
    "get_candidate_facing_error_entry",
]
