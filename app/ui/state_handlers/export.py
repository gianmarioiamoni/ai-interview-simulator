# app/ui/state_handlers/export.py

import os
from datetime import datetime

from domain.contracts.interview_state import InterviewState
from app.ui.dto.final_report_dto import FinalReportDTO
from services.report_export_service import ReportExportService


export_service = ReportExportService()


def export_pdf(state: InterviewState) -> str:
    if not state.is_completed:
        return ""

    report = FinalReportDTO.from_state(state)

    os.makedirs("/mnt/data", exist_ok=True)

    path = f"/mnt/data/{state.interview_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

    export_service.export_pdf(report, path)

    return path


def export_json(state: InterviewState) -> str:

    if not state.is_completed:
        return ""

    report = FinalReportDTO.from_state(state)

    os.makedirs("/mnt/data", exist_ok=True)

    path = f"/mnt/data/{state.interview_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    export_service.export_json(report, path)

    return path
