# app/ui/presentation/surface_phase.py
# EPIC-07 EC-SS-01 / Data Model §3.2 — closed SurfacePhase enum.

from __future__ import annotations

from enum import Enum


class SurfacePhase(str, Enum):
    """Closed presentation phase set for candidate surfaces (V-05)."""

    LOADING = "LOADING"
    EMPTY = "EMPTY"
    READY = "READY"
    ERROR = "ERROR"
