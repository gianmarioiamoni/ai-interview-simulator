# tests/domain/contracts/report/conftest.py
# Shared fixtures for Report contract tests — reuses SessionHistory fixtures

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.contracts.report.report import Report
from domain.contracts.report.report_builder import ReportBuilder

# Reuse upstream fixture helpers
from tests.domain.contracts.session_history.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    FIXED_HISTORY_DT,
    make_session_history,
)

REPORT_ID = "report-test-001"
FIXED_REPORT_DT = datetime(2026, 7, 3, 1, 0, 0, tzinfo=timezone.utc)


def make_report(
    report_id: str = REPORT_ID,
    session_id: str = SESSION_ID,
    candidate_id: str = CANDIDATE_ID,
) -> Report:
    history = make_session_history(
        session_id=session_id,
        candidate_id=candidate_id,
    )
    return (
        ReportBuilder()
        .with_session_history(history)
        .with_report_id(report_id)
        .with_created_at(FIXED_REPORT_DT)
        .build()
    )


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def candidate_id() -> str:
    return CANDIDATE_ID


@pytest.fixture
def session_id() -> str:
    return SESSION_ID


@pytest.fixture
def session_history():
    return make_session_history()


@pytest.fixture
def report() -> Report:
    return make_report()
