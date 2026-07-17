# app/ui/presentation/surface_state.py
# EPIC-07 EC-SS-01 / Data Model §4.2 — SurfaceState (UI-layer; ephemeral).

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.ui.presentation.candidate_facing_error import CandidateFacingError
from app.ui.presentation.surface_phase import SurfacePhase
from app.ui.presentation.surface_state_validation import (
    validate_empty_phase_coupling,
    validate_error_phase_coupling,
    validate_loader_allowed,
    validate_surface_id,
)


class SurfaceState(BaseModel):
    """Immutable presentation phase for one candidate surface (EC-SS-01)."""

    surface_id: str = Field(..., min_length=1)
    phase: SurfacePhase
    error: CandidateFacingError | None = None
    allows_loader: bool
    empty_copy_key: str | None = None

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def _validate_dm_v_ss(self) -> SurfaceState:
        validate_surface_id(self.surface_id)
        validate_error_phase_coupling(self.phase, self.error)
        validate_empty_phase_coupling(
            self.phase,
            self.empty_copy_key,
            surface_id=self.surface_id,
        )
        validate_loader_allowed(self.phase, self.allows_loader)
        return self
