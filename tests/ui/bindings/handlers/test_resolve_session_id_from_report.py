# tests/ui/bindings/handlers/test_resolve_session_id_from_report.py
# EPIC-V13-05 Phase 3 — I-C25-01 / I-C25-02: Report.session_id sole replay identifier.

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from app.ui.bindings.handlers.replay_layout_coordinator import (
    resolve_session_id_from_report,
)
from tests.domain.contracts.report.conftest import make_report
from tests.domain.contracts.session_history.conftest import make_session_history


class TestResolveSessionIdFromReport:

    def test_uses_report_session_id_exclusively(self) -> None:
        report = make_report(session_id="report-session-001")
        state = MagicMock()
        state.report = report
        state.session_history = make_session_history(session_id="history-session-999")
        state.interview_id = "interview-id-other"

        assert resolve_session_id_from_report(state) == "report-session-001"
        assert resolve_session_id_from_report(state) == report.session_id

    def test_ignores_session_history_when_report_present(self) -> None:
        report = make_report(session_id="from-report")
        history = make_session_history(session_id="from-history")
        state = MagicMock()
        state.report = report
        state.session_history = history
        state.interview_id = "from-interview"

        result = resolve_session_id_from_report(state)

        assert result == "from-report"
        assert result != history.session_id
        assert result != state.interview_id

    def test_rejects_when_report_is_none(self) -> None:
        state = MagicMock()
        state.report = None
        state.session_history = make_session_history()
        state.interview_id = "fallback-id"

        with pytest.raises(ValueError, match="Report is required"):
            resolve_session_id_from_report(state)

    def test_rejects_when_state_is_none(self) -> None:
        with pytest.raises(ValueError, match="InterviewState is required"):
            resolve_session_id_from_report(None)

    def test_does_not_prefer_session_history_over_report(self) -> None:
        """F-W-01: SessionHistory must not be preferred when Report is present."""
        report = make_report(session_id="canonical")
        state = MagicMock()
        state.report = report
        state.session_history = make_session_history(session_id="legacy-preferred")
        state.interview_id = "legacy-preferred"

        assert resolve_session_id_from_report(state) == "canonical"
