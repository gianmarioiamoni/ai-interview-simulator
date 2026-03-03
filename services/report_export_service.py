# app/services/report_export_service.py

import json
from typing import Any
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from reportlab.platypus import PageBreak

from reportlab.lib.pagesizes import A4


class ReportExportService:

    # ---------------------------------------------------------
    # PDF EXPORT
    # ---------------------------------------------------------

    def export_pdf(self, report: Any, file_path: str) -> str:

        doc = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []

        styles = getSampleStyleSheet()
        normal = styles["Normal"]
        heading = styles["Heading1"]

        elements.append(Paragraph("AI Interview Evaluation Report", heading))
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(Paragraph("Executive Summary:", styles["Heading2"]))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(report.executive_summary, normal))
        elements.append(Spacer(1, 0.3 * inch))

        # ---------------------------------------------------------
        # Overall metrics table
        # ---------------------------------------------------------

        data = [
            ["Overall Score", f"{report.overall_score}/100"],
            ["Hiring Probability", f"{report.hiring_probability}%"],
            ["Percentile Rank", f"{report.percentile_rank}%"],
            ["Confidence", f"{round(report.confidence.final * 100,1)}%"],
            ["Total Tokens Used", str(report.total_tokens_used)],
        ]

        table = Table(data, colWidths=[200, 200])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ]
            )
        )

        elements.append(Paragraph("Overall Metrics:", styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))

        # ---------------------------------------------------------
        # Dimension breakdown
        # ---------------------------------------------------------

        elements.append(Paragraph("Performance Dimensions:", styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))

        for dim in report.dimension_scores:
            elements.append(Paragraph(f"{dim.name}: {dim.score}/100", normal))

        elements.append(Spacer(1, 0.3 * inch))

        # ---------------------------------------------------------
        # Question assessments
        # ---------------------------------------------------------

        elements.append(Paragraph("Question-Level Assessment:", styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))

        for q in report.question_assessments:
            elements.append(
                Paragraph(
                    f"Question {q.question_id} - Score: {q.score}/100",
                    styles["Heading3"],
                )
            )
            elements.append(Paragraph(q.feedback, normal))
            elements.append(Spacer(1, 0.2 * inch))

        elements.append(PageBreak())

        # ---------------------------------------------------------
        # Improvements
        # ---------------------------------------------------------

        elements.append(Paragraph("Improvement Roadmap:", styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))

        improvement_items = [
            ListItem(Paragraph(i, normal)) for i in report.improvement_suggestions
        ]
        elements.append(ListFlowable(improvement_items, bulletType="bullet"))

        doc.build(elements)

        return file_path

    # ---------------------------------------------------------
    # JSON EXPORT
    # ---------------------------------------------------------

    def export_json(self, report: Any, file_path: str) -> str:

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=4)

        return file_path
