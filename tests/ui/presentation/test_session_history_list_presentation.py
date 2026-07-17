# tests/ui/presentation/test_session_history_list_presentation.py
# EPIC-07 P3/C6 — SessionHistoryListPresentation READY/EMPTY/ERROR.

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.ui.presentation import (
    AsyncBoundary,
    SessionHistoryItem,
    SessionHistoryListPresentation,
    SurfacePhase,
    emit_boundary_error,
    get_empty_copy_entry,
    load_session_history_list,
    present_session_history_list,
)


class TestSessionHistoryItem:
    def test_label_omits_null_date_and_role(self) -> None:
        item = SessionHistoryItem.from_session_ref("s1")
        assert item.display_label == "s1"
        assert item.session_date is None
        assert item.role_label is None

    def test_label_composes_role_and_date(self) -> None:
        item = SessionHistoryItem.from_session_ref(
            "s1",
            role_label="Backend",
            session_date="2026-07-15",
        )
        assert "Backend" in item.display_label
        assert "2026-07-15" in item.display_label
        assert "s1" in item.display_label
        assert "null" not in item.display_label.lower()


class TestSessionHistoryListPresentationContracts:
    def test_ready_allows_items_and_null_error(self) -> None:
        item = SessionHistoryItem.from_session_ref("s1")
        presentation = SessionHistoryListPresentation(
            items=(item,),
            phase=SurfacePhase.READY,
        )
        assert presentation.error is None
        assert presentation.empty_copy_key is None
        assert presentation.status_message() == ""
        assert presentation.dropdown_choices() == [(item.display_label, "s1")]

    def test_empty_requires_catalog_key(self) -> None:
        presentation = SessionHistoryListPresentation(
            items=(),
            phase=SurfacePhase.EMPTY,
            empty_copy_key="empty.history.none",
        )
        entry = get_empty_copy_entry("empty.history.none")
        assert presentation.status_message() == entry.message_text
        assert presentation.dropdown_choices() == []

    def test_empty_rejects_wrong_key_or_items(self) -> None:
        with pytest.raises(ValidationError, match="DM-V-SH-02"):
            SessionHistoryListPresentation(
                items=(),
                phase=SurfacePhase.EMPTY,
                empty_copy_key="empty.feedback.none",
            )
        with pytest.raises(ValidationError, match="DM-V-SH-02"):
            SessionHistoryListPresentation(
                items=(SessionHistoryItem.from_session_ref("s1"),),
                phase=SurfacePhase.EMPTY,
                empty_copy_key="empty.history.none",
            )

    def test_error_requires_session_history_load_boundary(self) -> None:
        error = emit_boundary_error(AsyncBoundary.SESSION_HISTORY_LOAD)
        presentation = SessionHistoryListPresentation(
            items=(),
            phase=SurfacePhase.ERROR,
            error=error,
        )
        assert presentation.status_message() == error.message_text

        wrong = emit_boundary_error(AsyncBoundary.REPORT_EXPORT)
        with pytest.raises(ValidationError, match="DM-V-SH-03"):
            SessionHistoryListPresentation(
                items=(),
                phase=SurfacePhase.ERROR,
                error=wrong,
            )

    def test_ready_forbids_error(self) -> None:
        with pytest.raises(ValidationError, match="DM-V-SH-01"):
            SessionHistoryListPresentation(
                items=(),
                phase=SurfacePhase.READY,
                error=emit_boundary_error(AsyncBoundary.SESSION_HISTORY_LOAD),
            )


class TestPresentSessionHistoryList:
    def test_success_non_empty_is_ready(self) -> None:
        presentation = present_session_history_list(
            lambda: (SessionHistoryItem.from_session_ref("s1"),)
        )
        assert presentation.phase is SurfacePhase.READY
        assert len(presentation.items) == 1

    def test_success_empty_is_empty_catalog(self) -> None:
        presentation = present_session_history_list(lambda: ())
        assert presentation.phase is SurfacePhase.EMPTY
        assert presentation.empty_copy_key == "empty.history.none"
        assert presentation.status_message() == get_empty_copy_entry(
            "empty.history.none"
        ).message_text

    def test_silent_none_forbidden_emits_error(self) -> None:
        presentation = present_session_history_list(lambda: None)
        assert presentation.phase is SurfacePhase.ERROR
        assert presentation.error is not None
        assert presentation.error.boundary is AsyncBoundary.SESSION_HISTORY_LOAD

    def test_fetch_exception_emits_error(self) -> None:
        def _fail():
            raise RuntimeError("repo boom")

        presentation = present_session_history_list(_fail)
        assert presentation.phase is SurfacePhase.ERROR
        assert presentation.error is not None
        assert presentation.error.boundary is AsyncBoundary.SESSION_HISTORY_LOAD

    def test_load_session_history_list_projects_presentation(self) -> None:
        result = load_session_history_list(lambda: ["s1", "s2"])
        assert result.presentation.phase is SurfacePhase.READY
        assert result.session_ids == ("s1", "s2")
        assert result.error is None

        empty = load_session_history_list(lambda: [])
        assert empty.presentation.phase is SurfacePhase.EMPTY
        assert empty.session_ids == ()

        none_result = load_session_history_list(lambda: None)
        assert none_result.presentation.phase is SurfacePhase.ERROR
        assert none_result.error is not None
