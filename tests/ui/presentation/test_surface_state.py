# tests/ui/presentation/test_surface_state.py
# EPIC-07 P1/C2 — SurfaceState + DM-V-SS helpers.

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.ui.presentation import (
    EMPTY_COPY_CATALOG,
    SURFACE_IDS,
    CandidateFacingError,
    SurfacePhase,
    SurfaceState,
    get_empty_copy_entry,
    validate_deterministic_surface_not_loading,
    validate_empty_phase_coupling,
    validate_error_phase_coupling,
    validate_loader_allowed,
)

_EXPECTED_PHASES = (
    SurfacePhase.LOADING,
    SurfacePhase.EMPTY,
    SurfacePhase.READY,
    SurfacePhase.ERROR,
)


def _error() -> CandidateFacingError:
    return CandidateFacingError.from_catalog("err.session_start.failed")


class TestSurfacePhaseClosed:
    def test_enum_member_count_is_four(self) -> None:
        assert len(SurfacePhase) == 4

    def test_enum_members_match_frozen_set(self) -> None:
        assert tuple(SurfacePhase) == _EXPECTED_PHASES


class TestEmptyCopyCatalog:
    def test_catalog_keys_match_data_model(self) -> None:
        assert set(EMPTY_COPY_CATALOG) == {
            "empty.report.unavailable",
            "empty.replay.no_questions",
            "empty.progress.insufficient",
            "empty.history.none",
            "empty.feedback.none",
            "empty.question.none",
        }

    def test_catalog_key_maps_to_text(self) -> None:
        entry = get_empty_copy_entry("empty.history.none")
        assert entry.surface_id == "history"
        assert entry.message_text == "No previous sessions yet."


class TestSurfaceIds:
    def test_surface_id_catalog_closed(self) -> None:
        assert SURFACE_IDS == frozenset(
            {
                "setup",
                "question",
                "feedback",
                "report",
                "replay",
                "progress",
                "history",
            }
        )


class TestDmVSsHelpers:
    def test_error_phase_requires_error(self) -> None:
        with pytest.raises(ValueError, match="DM-V-SS-01"):
            validate_error_phase_coupling(SurfacePhase.ERROR, None)

    def test_error_forbidden_outside_error_phase(self) -> None:
        with pytest.raises(ValueError, match="DM-V-SS-01"):
            validate_error_phase_coupling(SurfacePhase.READY, _error())

    def test_empty_phase_requires_empty_copy_key(self) -> None:
        with pytest.raises(ValueError, match="DM-V-SS-02"):
            validate_empty_phase_coupling(
                SurfacePhase.EMPTY,
                None,
                surface_id="history",
            )

    def test_empty_copy_key_forbidden_outside_empty_phase(self) -> None:
        with pytest.raises(ValueError, match="DM-V-SS-02"):
            validate_empty_phase_coupling(
                SurfacePhase.READY,
                "empty.history.none",
                surface_id="history",
            )

    def test_loader_forbidden_when_allows_loader_false(self) -> None:
        with pytest.raises(ValueError, match="DM-V-SS-04"):
            validate_loader_allowed(SurfacePhase.LOADING, False)

    @pytest.mark.parametrize("surface_id", ("report", "replay", "progress"))
    def test_deterministic_data_ready_forbids_loading(self, surface_id: str) -> None:
        with pytest.raises(ValueError, match="DM-V-SS-03"):
            validate_deterministic_surface_not_loading(
                surface_id,
                SurfacePhase.LOADING,
                data_ready=True,
            )

    def test_deterministic_not_ready_may_load(self) -> None:
        validate_deterministic_surface_not_loading(
            "report",
            SurfacePhase.LOADING,
            data_ready=False,
        )


class TestSurfaceStateContracts:
    def test_ready_surface(self) -> None:
        state = SurfaceState(
            surface_id="question",
            phase=SurfacePhase.READY,
            allows_loader=True,
        )
        assert state.error is None
        assert state.empty_copy_key is None

    def test_error_requires_error_field(self) -> None:
        with pytest.raises(ValidationError, match="DM-V-SS-01"):
            SurfaceState(
                surface_id="setup",
                phase=SurfacePhase.ERROR,
                allows_loader=True,
            )

    def test_error_phase_accepts_candidate_facing_error(self) -> None:
        state = SurfaceState(
            surface_id="setup",
            phase=SurfacePhase.ERROR,
            error=_error(),
            allows_loader=True,
        )
        assert state.error is not None
        assert state.empty_copy_key is None

    def test_error_forbidden_on_ready(self) -> None:
        with pytest.raises(ValidationError, match="DM-V-SS-01"):
            SurfaceState(
                surface_id="question",
                phase=SurfacePhase.READY,
                error=_error(),
                allows_loader=True,
            )

    def test_empty_requires_empty_copy_key(self) -> None:
        with pytest.raises(ValidationError, match="DM-V-SS-02"):
            SurfaceState(
                surface_id="history",
                phase=SurfacePhase.EMPTY,
                allows_loader=False,
            )

    def test_empty_accepts_matching_catalog_key(self) -> None:
        state = SurfaceState(
            surface_id="history",
            phase=SurfacePhase.EMPTY,
            allows_loader=False,
            empty_copy_key="empty.history.none",
        )
        assert state.empty_copy_key == "empty.history.none"
        assert state.error is None

    def test_empty_copy_key_forbidden_on_ready(self) -> None:
        with pytest.raises(ValidationError, match="DM-V-SS-02"):
            SurfaceState(
                surface_id="history",
                phase=SurfacePhase.READY,
                allows_loader=False,
                empty_copy_key="empty.history.none",
            )

    def test_empty_copy_key_must_match_surface_id(self) -> None:
        with pytest.raises(ValidationError, match="DM-V-SS-02"):
            SurfaceState(
                surface_id="report",
                phase=SurfacePhase.EMPTY,
                allows_loader=False,
                empty_copy_key="empty.history.none",
            )

    def test_loading_forbidden_when_allows_loader_false(self) -> None:
        with pytest.raises(ValidationError, match="DM-V-SS-04"):
            SurfaceState(
                surface_id="setup",
                phase=SurfacePhase.LOADING,
                allows_loader=False,
            )

    def test_loading_allowed_when_allows_loader_true(self) -> None:
        state = SurfaceState(
            surface_id="setup",
            phase=SurfacePhase.LOADING,
            allows_loader=True,
        )
        assert state.phase is SurfacePhase.LOADING

    def test_unknown_surface_id_rejected(self) -> None:
        with pytest.raises(ValidationError, match="SM-06"):
            SurfaceState(
                surface_id="dashboard",
                phase=SurfacePhase.READY,
                allows_loader=False,
            )

    def test_immutable_and_extra_forbid(self) -> None:
        state = SurfaceState(
            surface_id="feedback",
            phase=SurfacePhase.READY,
            allows_loader=True,
        )
        with pytest.raises(ValidationError):
            state.phase = SurfacePhase.EMPTY  # type: ignore[misc]
        with pytest.raises(ValidationError):
            SurfaceState(
                surface_id="feedback",
                phase=SurfacePhase.READY,
                allows_loader=True,
                placeholder=True,  # type: ignore[call-arg]
            )
