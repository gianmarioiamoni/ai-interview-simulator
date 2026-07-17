# app/ui/presentation/session_history_list_presentation.py
# EPIC-07 EC-SH-01 / Data Model §4.5 — SessionHistory list presentation (UI-layer).

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.ui.presentation.async_boundary import AsyncBoundary
from app.ui.presentation.candidate_facing_error import CandidateFacingError
from app.ui.presentation.empty_copy_catalog import get_empty_copy_entry
from app.ui.presentation.surface_phase import SurfacePhase

_HISTORY_EMPTY_KEY = "empty.history.none"


class SessionHistoryItem(BaseModel):
    """Single replayable session row for the history list (EC-SH-01 item)."""

    session_id: str = Field(..., min_length=1)
    display_label: str = Field(..., min_length=1)
    session_date: str | None = None
    role_label: str | None = None

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_session_ref(
        cls,
        session_id: str,
        *,
        session_date: str | None = None,
        role_label: str | None = None,
    ) -> SessionHistoryItem:
        """Build a candidate-safe list item; omit null date/role from the label."""
        if not session_id or not str(session_id).strip():
            raise ValueError("session_id must be non-empty.")
        parts: list[str] = []
        if role_label and role_label.strip():
            parts.append(role_label.strip())
        if session_date and session_date.strip():
            parts.append(session_date.strip())
        display_label = " · ".join(parts) if parts else session_id
        if parts:
            display_label = f"{display_label} ({session_id})"
        return cls(
            session_id=session_id,
            display_label=display_label,
            session_date=session_date,
            role_label=role_label,
        )


class SessionHistoryListPresentation(BaseModel):
    """Ephemeral history list surface: READY / EMPTY / ERROR (EC-SH-01)."""

    items: tuple[SessionHistoryItem, ...] = ()
    phase: SurfacePhase
    error: CandidateFacingError | None = None
    empty_copy_key: str | None = None

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def _validate_dm_v_sh(self) -> SessionHistoryListPresentation:
        if self.phase is SurfacePhase.LOADING:
            raise ValueError(
                "SessionHistoryListPresentation does not use LOADING in EPIC-07 C6; "
                "use EMPTY, READY, or ERROR."
            )
        if self.phase is SurfacePhase.READY:
            if self.error is not None:
                raise ValueError("DM-V-SH-01: phase=READY requires error is null.")
            if self.empty_copy_key is not None:
                raise ValueError("phase=READY forbids empty_copy_key.")
            return self
        if self.phase is SurfacePhase.EMPTY:
            if self.items != ():
                raise ValueError("DM-V-SH-02: phase=EMPTY requires items == ().")
            if self.empty_copy_key != _HISTORY_EMPTY_KEY:
                raise ValueError(
                    "DM-V-SH-02: phase=EMPTY requires empty_copy_key='empty.history.none'."
                )
            if self.error is not None:
                raise ValueError("phase=EMPTY forbids error.")
            get_empty_copy_entry(self.empty_copy_key)
            return self
        if self.phase is SurfacePhase.ERROR:
            if self.error is None:
                raise ValueError("DM-V-SH-03: phase=ERROR requires error.")
            if self.error.boundary is not AsyncBoundary.SESSION_HISTORY_LOAD:
                raise ValueError(
                    "DM-V-SH-03: phase=ERROR requires boundary=SESSION_HISTORY_LOAD."
                )
            if self.empty_copy_key is not None:
                raise ValueError("phase=ERROR forbids empty_copy_key.")
            return self
        raise ValueError(f"Unsupported phase={self.phase!r}.")

    def status_message(self) -> str:
        """Candidate-facing status copy for EMPTY/ERROR; empty string when READY."""
        if self.phase is SurfacePhase.EMPTY:
            return get_empty_copy_entry(self.empty_copy_key or _HISTORY_EMPTY_KEY).message_text
        if self.phase is SurfacePhase.ERROR and self.error is not None:
            return self.error.message_text
        return ""

    def dropdown_choices(self) -> list[tuple[str, str]]:
        """Gradio Dropdown choices as (label, session_id)."""
        if self.phase is not SurfacePhase.READY:
            return []
        return [(item.display_label, item.session_id) for item in self.items]
