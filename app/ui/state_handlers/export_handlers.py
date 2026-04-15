# app/ui/state_handlers/export_handlers.py

import gradio as gr
from datetime import datetime, timezone

from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from services.report_export_service import ReportExportService


def export_pdf_handler(state):

    if state is None:
        return gr.update(value=None, visible=False)

    mapper = InterviewStateMapper()
    report = mapper.to_final_report_dto(state)

    service = ReportExportService()
    file_path = f"/tmp/report_{state.interview_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"

    path = service.export_pdf(report, file_path)

    return gr.update(value=path, visible=True)


def export_json_handler(state):

    if state is None:
        return gr.update(value=None, visible=False)

    mapper = InterviewStateMapper()
    report = mapper.to_final_report_dto(state)

    service = ReportExportService()
    file_path = f"/tmp/report_{state.interview_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

    path = service.export_json(report, file_path)

    return gr.update(value=path, visible=True)
