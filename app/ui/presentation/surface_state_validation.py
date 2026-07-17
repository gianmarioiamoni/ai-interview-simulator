# app/ui/presentation/surface_state_validation.py
# EPIC-07 Data Model §4.2 — DM-V-SS validation helpers.

from __future__ import annotations

from app.ui.presentation.empty_copy_catalog import get_empty_copy_entry
from app.ui.presentation.surface_ids import DETERMINISTIC_SURFACE_IDS, SURFACE_IDS
from app.ui.presentation.surface_phase import SurfacePhase


def validate_surface_id(surface_id: str) -> None:
    """Fail-fast when ``surface_id`` is outside the closed §3.4 catalog (SM-06)."""
    if surface_id not in SURFACE_IDS:
        raise ValueError(f"Unknown surface_id={surface_id!r} (SM-06).")


def validate_error_phase_coupling(
    phase: SurfacePhase,
    error: object | None,
) -> None:
    """DM-V-SS-01: ``phase=ERROR`` ↔ ``error != null``."""
    if phase is SurfacePhase.ERROR and error is None:
        raise ValueError("DM-V-SS-01: phase=ERROR requires error.")
    if phase is not SurfacePhase.ERROR and error is not None:
        raise ValueError("DM-V-SS-01: error is forbidden unless phase=ERROR.")


def validate_empty_phase_coupling(
    phase: SurfacePhase,
    empty_copy_key: str | None,
    *,
    surface_id: str,
) -> None:
    """DM-V-SS-02: ``phase=EMPTY`` ↔ ``empty_copy_key != null`` (+ catalog / surface match)."""
    if phase is SurfacePhase.EMPTY:
        if empty_copy_key is None:
            raise ValueError("DM-V-SS-02: phase=EMPTY requires empty_copy_key.")
        entry = get_empty_copy_entry(empty_copy_key)
        if entry.surface_id != surface_id:
            raise ValueError(
                f"DM-V-SS-02: empty_copy_key={empty_copy_key!r} belongs to "
                f"surface_id={entry.surface_id!r}, not {surface_id!r}."
            )
        return
    if empty_copy_key is not None:
        raise ValueError("DM-V-SS-02: empty_copy_key is forbidden unless phase=EMPTY.")


def validate_loader_allowed(phase: SurfacePhase, allows_loader: bool) -> None:
    """DM-V-SS-04: ``allows_loader=False`` ⇒ ``phase ≠ LOADING``."""
    if not allows_loader and phase is SurfacePhase.LOADING:
        raise ValueError("DM-V-SS-04: phase=LOADING forbidden when allows_loader=False.")


def validate_deterministic_surface_not_loading(
    surface_id: str,
    phase: SurfacePhase,
    *,
    data_ready: bool,
) -> None:
    """DM-V-SS-03: deterministic surface + data-ready ⇒ ``phase ≠ LOADING``."""
    if (
        data_ready
        and surface_id in DETERMINISTIC_SURFACE_IDS
        and phase is SurfacePhase.LOADING
    ):
        raise ValueError(
            f"DM-V-SS-03: surface_id={surface_id!r} with data-ready "
            "must not use phase=LOADING."
        )
