# app/services/report_export_service.py
# EPIC-06 C8 — C-26 export parity (X-08): same FinalReportDTO + build_report_markdown path as UI.

# Report export service
#
# HTML → PDF rendering using WeasyPrint
# Ensures visual consistency with UI report (explainability fields included)

import json
import logging

try:
    from weasyprint import HTML as _WeasyprintHTML
    _WEASYPRINT_AVAILABLE = True
except OSError:
    _WEASYPRINT_AVAILABLE = False
    _WeasyprintHTML = None  # type: ignore

HTML = _WeasyprintHTML

from app.ui.views.report_view import build_report_markdown
from app.ui.dto.final_report_dto import FinalReportDTO

logger = logging.getLogger(__name__)


class ReportExportService:

    # ---------------------------------------------------------
    # PDF EXPORT (HTML → PDF)
    # ---------------------------------------------------------

    def export_pdf(self, report: FinalReportDTO, file_path: str) -> str:

        if not _WEASYPRINT_AVAILABLE:
            raise RuntimeError(
                "PDF export is unavailable: WeasyPrint native libraries are not installed on this system."
            )

        html_content = self.build_export_html(report)

        try:
            HTML(string=html_content).write_pdf(file_path)  # type: ignore[misc]
        except Exception:
            logger.exception("WeasyPrint PDF generation failed for %s", file_path)
            raise

        return file_path

    # ---------------------------------------------------------
    # JSON EXPORT
    # ---------------------------------------------------------

    def export_json(self, report: FinalReportDTO, file_path: str) -> str:

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(mode="json"), f, indent=4)

        return file_path

    # ---------------------------------------------------------
    # HTML EXPORT BODY (X-08 parity with UI render path)
    # ---------------------------------------------------------

    def build_export_html(self, report: FinalReportDTO) -> str:
        """Build full HTML document from FinalReportDTO (same factory path as UI)."""
        return self._build_full_html(report)

    # ---------------------------------------------------------
    # INTERNAL: FULL HTML DOCUMENT
    # ---------------------------------------------------------

    def _build_full_html(self, report: FinalReportDTO) -> str:
        # X-08: identical DTO → build_report_markdown path as report HTML UI.
        body = build_report_markdown(report)

        return f"""
<html>
<head>
    <meta charset="utf-8">

    <style>
        body {{
            font-family: Arial, sans-serif;
            padding: 30px;
            line-height: 1.5;
        }}

        h1, h2, h3, h4 {{
            margin-top: 24px;
            margin-bottom: 10px;
        }}

        p {{
            margin: 6px 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            margin-bottom: 20px;
            font-size: 12px;
        }}

        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}

        th {{
            background-color: #f5f5f5;
            font-weight: bold;
        }}

        span {{
            display: inline-block;
            margin-top: 4px;
        }}

        img {{
            max-width: 100%;
            height: auto;
            margin-top: 10px;
        }}

        /* Prevent bad page breaks */
        table, img, div {{
            page-break-inside: avoid;
        }}

        h2, h3 {{
            page-break-after: avoid;
        }}

    </style>
</head>

<body>
{body}
</body>
</html>
"""
