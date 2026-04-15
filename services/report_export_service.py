# app/services/report_export_service.py

# Report export service
#
# HTML → PDF rendering using WeasyPrint
# Ensures visual consistency with UI report

import json
from typing import Any

from weasyprint import HTML

from app.ui.views.report_view import build_report_markdown


class ReportExportService:

    # ---------------------------------------------------------
    # PDF EXPORT (HTML → PDF)
    # ---------------------------------------------------------

    def export_pdf(self, report: Any, file_path: str) -> str:

        html_content = self._build_full_html(report)

        HTML(string=html_content).write_pdf(file_path)

        return file_path

    # ---------------------------------------------------------
    # JSON EXPORT
    # ---------------------------------------------------------

    def export_json(self, report: Any, file_path: str) -> str:

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=4)

        return file_path

    # ---------------------------------------------------------
    # INTERNAL: FULL HTML DOCUMENT
    # ---------------------------------------------------------

    def _build_full_html(self, report: Any) -> str:

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
