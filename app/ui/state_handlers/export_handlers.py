# app/ui/state_handlers/export_handlers.py
# EPIC-06 C8 — C-26 export handlers consume FinalReportDTO via sole from_report factory (X-08).
# EPIC-07 C4 — REPORT_EXPORT emits CandidateFacingError (catalog message).

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import gradio as gr

from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from app.ui.presentation.async_boundary import AsyncBoundary
from app.ui.presentation.boundary_error_emission import emit_boundary_error
from services.report_export_service import ReportExportService

logger = logging.getLogger(__name__)

_mapper = InterviewStateMapper()
_service = ReportExportService()


def _download_button(*, value: Any, visible: bool) -> Any:
    factory = getattr(gr, "DownloadButton", None)
    if factory is None:
        return {"value": value, "visible": visible}
    return factory(value=value, visible=visible)


def _emit_report_export_failure():
    error = emit_boundary_error(AsyncBoundary.REPORT_EXPORT)
    warn = getattr(gr, "Warning", None)
    if callable(warn):
        warn(error.message_text)
    return error


def export_pdf_handler(state) -> Any:

    if state is None or not state.is_completed:
        return _download_button(value=None, visible=False)

    try:
        report = _mapper.to_final_report_dto(state)
        file_path = f"/tmp/report_{state.interview_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
        path = _service.export_pdf(report, file_path)
        return _download_button(value=path, visible=True)
    except Exception:
        logger.exception("PDF export failed (REPORT_EXPORT)")
        _emit_report_export_failure()
        return _download_button(value=None, visible=True)


def export_json_handler(state) -> Any:

    if state is None or not state.is_completed:
        return _download_button(value=None, visible=False)

    try:
        report = _mapper.to_final_report_dto(state)
        file_path = f"/tmp/report_{state.interview_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        path = _service.export_json(report, file_path)
        return _download_button(value=path, visible=True)
    except Exception:
        logger.exception("JSON export failed (REPORT_EXPORT)")
        _emit_report_export_failure()
        return _download_button(value=None, visible=True)
