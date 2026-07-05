# tests/services/test_report_export_service.py

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from services.report_export_service import ReportExportService
from tests.factories.interview_state_factory import build_state_with_execution
from tests.ui.mappers.test_interview_state_mapper import build_interview_evaluation
from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from tests.domain.contracts.report.conftest import make_report


def _build_completed_report():
    state = build_state_with_execution(passed_tests=2, total_tests=2)
    state = state.model_copy(
        update={
            "interview_evaluation": build_interview_evaluation(),
            "is_completed": True,
            "report": make_report(),
        }
    )
    return InterviewStateMapper().to_final_report_dto(state)


# ---------------------------------------------------------
# PDF EXPORT
# ---------------------------------------------------------


def test_export_pdf_creates_file_with_pdf_extension():
    report = _build_completed_report()
    service = ReportExportService()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report.pdf")
        with patch("services.report_export_service.HTML") as mock_html:
            mock_html.return_value.write_pdf = MagicMock()
            result = service.export_pdf(report, path)

        assert result == path
        assert result.endswith(".pdf")
        mock_html.return_value.write_pdf.assert_called_once_with(path)


def test_export_pdf_raises_and_logs_on_weasyprint_failure():
    report = _build_completed_report()
    service = ReportExportService()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report.pdf")
        with patch("services.report_export_service.HTML") as mock_html:
            mock_html.return_value.write_pdf.side_effect = RuntimeError("font error")
            with pytest.raises(RuntimeError, match="font error"):
                service.export_pdf(report, path)


# ---------------------------------------------------------
# JSON EXPORT
# ---------------------------------------------------------


def test_export_json_creates_valid_json_file():
    report = _build_completed_report()
    service = ReportExportService()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report.json")
        result = service.export_json(report, path)

    assert result == path


def test_export_json_file_contains_expected_fields():
    report = _build_completed_report()
    service = ReportExportService()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report.json")
        service.export_json(report, path)

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

    assert "overall_score" in data
    assert "hire_decision" in data
    assert "improvement_suggestions" in data
    assert "dimension_scores" in data


def test_export_json_serializes_enums_without_error():
    report = _build_completed_report()
    service = ReportExportService()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report.json")
        service.export_json(report, path)

        with open(path, encoding="utf-8") as f:
            raw = f.read()

    data = json.loads(raw)
    assert isinstance(data["role"], str)


# ---------------------------------------------------------
# EXPORT HANDLERS
# ---------------------------------------------------------


def _import_handlers():
    """Import export handlers directly, bypassing the state_handlers __init__
    which triggers start.py → langchain_openai → torch (SEGFAULT on Python 3.13 + anaconda)."""
    import sys
    import importlib
    from unittest.mock import MagicMock

    gr_mock = MagicMock()
    gr_mock.DownloadButton = MagicMock(side_effect=lambda **kw: kw)

    # Ensure start.py import chain is blocked
    for blocked in (
        "app.ui.state_handlers.start",
        "app.ui.state_handlers",
    ):
        sys.modules.pop(blocked, None)

    sys.modules["gradio"] = gr_mock

    # Remove cached handler module to force fresh import with new gradio mock
    sys.modules.pop("app.ui.state_handlers.export_handlers", None)

    import app.ui.state_handlers.export_handlers as handlers

    return handlers, gr_mock


def test_export_pdf_handler_returns_hidden_when_state_is_none():
    handlers, gr_mock = _import_handlers()
    handlers.export_pdf_handler(None)
    gr_mock.DownloadButton.assert_called_with(value=None, visible=False)


def test_export_json_handler_returns_hidden_when_state_is_none():
    handlers, gr_mock = _import_handlers()
    handlers.export_json_handler(None)
    gr_mock.DownloadButton.assert_called_with(value=None, visible=False)


def test_export_pdf_handler_returns_hidden_when_interview_not_completed():
    handlers, gr_mock = _import_handlers()
    state = build_state_with_execution(passed_tests=2, total_tests=2)
    # is_completed defaults to False
    handlers.export_pdf_handler(state)
    gr_mock.DownloadButton.assert_called_with(value=None, visible=False)


def test_export_pdf_handler_calls_service_and_returns_visible_on_success():
    handlers, gr_mock = _import_handlers()
    state = build_state_with_execution(passed_tests=2, total_tests=2)
    state = state.model_copy(
        update={
            "interview_evaluation": build_interview_evaluation(),
            "is_completed": True,
            "report": make_report(),
        }
    )
    with patch.object(handlers, "_service") as mock_svc:
        mock_svc.export_pdf.return_value = "/tmp/report_test.pdf"
        handlers.export_pdf_handler(state)
    gr_mock.DownloadButton.assert_called_with(value="/tmp/report_test.pdf", visible=True)


def test_export_pdf_handler_keeps_button_visible_on_failure():
    handlers, gr_mock = _import_handlers()
    state = build_state_with_execution(passed_tests=2, total_tests=2)
    state = state.model_copy(
        update={
            "interview_evaluation": build_interview_evaluation(),
            "is_completed": True,
            "report": make_report(),
        }
    )
    with patch.object(handlers, "_service") as mock_svc:
        mock_svc.export_pdf.side_effect = RuntimeError("font error")
        handlers.export_pdf_handler(state)
    gr_mock.DownloadButton.assert_called_with(value=None, visible=True)


def test_export_pdf_handler_shows_warning_on_failure():
    handlers, gr_mock = _import_handlers()
    state = build_state_with_execution(passed_tests=2, total_tests=2)
    state = state.model_copy(
        update={
            "interview_evaluation": build_interview_evaluation(),
            "is_completed": True,
            "report": make_report(),
        }
    )
    with patch.object(handlers, "_service") as mock_svc:
        mock_svc.export_pdf.side_effect = RuntimeError("font error")
        handlers.export_pdf_handler(state)
    gr_mock.Warning.assert_called_once()


def test_export_json_handler_keeps_button_visible_on_failure():
    handlers, gr_mock = _import_handlers()
    state = build_state_with_execution(passed_tests=2, total_tests=2)
    state = state.model_copy(
        update={
            "interview_evaluation": build_interview_evaluation(),
            "is_completed": True,
            "report": make_report(),
        }
    )
    with patch.object(handlers, "_service") as mock_svc:
        mock_svc.export_json.side_effect = OSError("disk full")
        handlers.export_json_handler(state)
    gr_mock.DownloadButton.assert_called_with(value=None, visible=True)


def test_export_json_handler_shows_warning_on_failure():
    handlers, gr_mock = _import_handlers()
    state = build_state_with_execution(passed_tests=2, total_tests=2)
    state = state.model_copy(
        update={
            "interview_evaluation": build_interview_evaluation(),
            "is_completed": True,
            "report": make_report(),
        }
    )
    with patch.object(handlers, "_service") as mock_svc:
        mock_svc.export_json.side_effect = OSError("disk full")
        handlers.export_json_handler(state)
    gr_mock.Warning.assert_called_once()


def test_export_json_handler_calls_service_and_returns_visible_on_success():
    handlers, gr_mock = _import_handlers()
    state = build_state_with_execution(passed_tests=2, total_tests=2)
    state = state.model_copy(
        update={
            "interview_evaluation": build_interview_evaluation(),
            "is_completed": True,
            "report": make_report(),
        }
    )
    with patch.object(handlers, "_service") as mock_svc:
        mock_svc.export_json.return_value = "/tmp/report_test.json"
        handlers.export_json_handler(state)
    gr_mock.DownloadButton.assert_called_with(value="/tmp/report_test.json", visible=True)
