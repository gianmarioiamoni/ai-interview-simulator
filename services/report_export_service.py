# app/services/report_export_service.py

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
        }}

        h1, h2, h3, h4 {{
            margin-top: 20px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}

        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
        }}

        th {{
            background-color: #f5f5f5;
        }}

        span {{
            display: inline-block;
            margin-top: 4px;
        }}
    </style>
</head>
<body>
{body}
</body>
</html>
"""
