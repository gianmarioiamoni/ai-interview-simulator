# app/ui/presentation/__init__.py
# EPIC-07 P1 — presentation-plane primitives (UI-layer; non-persistent).

from app.ui.presentation.async_boundary import AsyncBoundary
from app.ui.presentation.candidate_facing_error import CandidateFacingError
from app.ui.presentation.candidate_facing_error_catalog import (
    CANDIDATE_FACING_ERROR_CATALOG,
    CandidateFacingErrorCatalogEntry,
    get_candidate_facing_error_entry,
)
from app.ui.presentation.empty_copy_catalog import (
    EMPTY_COPY_CATALOG,
    EmptyCopyCatalogEntry,
    get_empty_copy_entry,
)
from app.ui.presentation.surface_ids import DETERMINISTIC_SURFACE_IDS, SURFACE_IDS
from app.ui.presentation.surface_phase import SurfacePhase
from app.ui.presentation.surface_state import SurfaceState
from app.ui.presentation.surface_state_validation import (
    validate_deterministic_surface_not_loading,
    validate_empty_phase_coupling,
    validate_error_phase_coupling,
    validate_loader_allowed,
    validate_surface_id,
)

__all__ = [
    "AsyncBoundary",
    "CandidateFacingError",
    "CANDIDATE_FACING_ERROR_CATALOG",
    "CandidateFacingErrorCatalogEntry",
    "get_candidate_facing_error_entry",
    "EMPTY_COPY_CATALOG",
    "EmptyCopyCatalogEntry",
    "get_empty_copy_entry",
    "SURFACE_IDS",
    "DETERMINISTIC_SURFACE_IDS",
    "SurfacePhase",
    "SurfaceState",
    "validate_surface_id",
    "validate_error_phase_coupling",
    "validate_empty_phase_coupling",
    "validate_loader_allowed",
    "validate_deterministic_surface_not_loading",
]
