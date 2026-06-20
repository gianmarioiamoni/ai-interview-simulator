# app/ui/state_handlers/export_handlers.py

import logging
import gradio as gr
from datetime import datetime, timezone

from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from services.report_export_service import ReportExportService

logger = logging.getLogger(__name__)

_mapper = InterviewStateMapper()
_service = ReportExportService()


def export_pdf_handler(state) -> gr.DownloadButton:

    if state is None or not state.is_completed:
        return gr.DownloadButton(value=None, visible=False)

    try:
        report = _mapper.to_final_report_dto(state)
        file_path = f"/tmp/report_{state.interview_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
        path = _service.export_pdf(report, file_path)
        return gr.DownloadButton(value=path, visible=True)
    except Exception:
        logger.exception("PDF export failed")
        gr.Warning("PDF export failed. Please try again.")
        return gr.DownloadButton(value=None, visible=True)


def export_json_handler(state) -> gr.DownloadButton:

    if state is None or not state.is_completed:
        return gr.DownloadButton(value=None, visible=False)

    try:
        report = _mapper.to_final_report_dto(state)
        file_path = f"/tmp/report_{state.interview_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        path = _service.export_json(report, file_path)
        return gr.DownloadButton(value=path, visible=True)
    except Exception:
        logger.exception("JSON export failed")
        gr.Warning("JSON export failed. Please try again.")
        return gr.DownloadButton(value=None, visible=True)
