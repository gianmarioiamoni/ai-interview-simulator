# tests/performance/test_slo_r_close_report.py
# EPIC-V13-09 C3 — SLO-R measurability: session_close→report < 3s; excludes longitudinal/DTO.

from __future__ import annotations

import inspect

from tests.performance import slo_r
from tests.performance.slo_r import (
    SLO_R_TARGET_MS,
    build_completed_state_for_slo_r,
    measure_close_report_ms,
    run_close_report_span,
)


def test_close_report_span_is_measurable_under_3s() -> None:
    """AR-03 / SLO-R: contiguous close→report wall-clock < 3s under harness."""
    result, elapsed_ms = measure_close_report_ms()

    assert elapsed_ms >= 0.0
    assert elapsed_ms < SLO_R_TARGET_MS
    assert result.session_history is not None
    assert result.report is not None


def test_close_report_uses_five_written_questions() -> None:
    """Implementation Plan §3 synthetic session shape (written-heavy, N=5)."""
    state = build_completed_state_for_slo_r()
    assert len(state.questions) == 5
    assert all(q.type.value == "written" for q in state.questions)
    assert state.is_completed is True


def test_span_excludes_longitudinal_ui_and_dto() -> None:
    """MEAS-05: harness span is close+report nodes only."""
    imported_modules = {
        name
        for name, module in inspect.getmembers(slo_r, inspect.ismodule)
        if module is not None
    }
    import_block = "\n".join(
        line
        for line in inspect.getsource(slo_r).splitlines()
        if line.startswith("from ") or line.startswith("import ")
    )
    assert "longitudinal" not in import_block
    assert "FinalReportDTO" not in import_block
    assert "UIResponseBuilder" not in import_block
    assert "interview_state_mapper" not in import_block
    assert "interview_graph" not in import_block
    assert "session_close_node" in import_block
    assert "report_node" in import_block
    assert "app.graph.nodes.longitudinal_update_node" not in imported_modules


def test_run_close_report_span_produces_report() -> None:
    state = build_completed_state_for_slo_r()
    result = run_close_report_span(state)
    assert result.session_history is not None
    assert result.report is not None
