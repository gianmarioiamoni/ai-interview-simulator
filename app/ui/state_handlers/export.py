# app/ui/state_handlers/export.py

import os
from datetime import datetime, timezone

from domain.contracts.interview_state import InterviewState
from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from services.report_export_service import ReportExportService


export_service = ReportExportService()
mapper = InterviewStateMapper()


def export_pdf(state: InterviewState) -> str:

    if not state.is_completed:
        raise ValueError("Interview not completed")

    report = mapper.to_final_report_dto(state)

    os.makedirs("/mnt/data", exist_ok=True)

    path = f"/mnt/data/{state.interview_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

    export_service.export_pdf(report, path)

    return path


def export_json(state: InterviewState) -> str:

    if not state.is_completed:
        raise ValueError("Interview not completed")

    report = mapper.to_final_report_dto(state)

    os.makedirs("/mnt/data", exist_ok=True)

    path = f"/mnt/data/{state.interview_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

    export_service.export_json(report, path)

    return path
