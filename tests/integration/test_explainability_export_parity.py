# tests/integration/test_explainability_export_parity.py
# EPIC-06 M3 / C8 — IT-05 export markdown/HTML parity for explainability fields (X-08).

from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.views.report_view import build_report_markdown
from services.report_export_service import ReportExportService
from tests.domain.contracts.report.conftest import (
    make_report,
    make_report_with_explainability,
)


class TestExplainabilityExportParity:
    """IT-05 — from_report → export HTML/JSON carries same explainability fields as UI HTML."""

    def test_export_html_matches_ui_html_explainability_fields(self) -> None:
        dto = FinalReportDTO.from_report(make_report_with_explainability())
        assert len(dto.narrative_insights) >= 1
        assert len(dto.coaching_actions) >= 1

        ui_html = build_report_markdown(dto)
        export_html = ReportExportService().build_export_html(dto)

        insight = dto.narrative_insights[0]
        action = dto.coaching_actions[0]
        feature_label = insight.source_feature_id.feature_type_id.replace(
            "_", " "
        ).title()
        category_label = insight.source_feature_id.semantic_category.replace(
            "_", " "
        ).title()
        origin_feature_label = action.origin_feature_type.replace("_", " ").title()

        for html in (ui_html, export_html):
            assert "Evidence:" in html
            assert "Traceable" in html
            assert insight.prose in html
            assert feature_label in html
            assert category_label in html
            assert "Origin:" in html
            assert "Supporting observations:" in html
            assert "Objective:" in html
            assert action.description in html
            assert action.origin_objective_description in html
            assert origin_feature_label in html

        # X-08: export wraps the same body content produced for UI.
        assert ui_html in export_html

    def test_export_html_empty_explainability_matches_ui(self) -> None:
        dto = FinalReportDTO.from_report(make_report())
        assert dto.narrative_insights == []
        assert dto.coaching_actions == []

        ui_html = build_report_markdown(dto)
        export_html = ReportExportService().build_export_html(dto)

        assert "Evidence:" not in ui_html
        assert "Evidence:" not in export_html
        assert "Coaching Actions" not in ui_html
        assert "Coaching Actions" not in export_html
        assert ui_html in export_html

    def test_export_json_includes_insight_evidence_fields(self) -> None:
        dto = FinalReportDTO.from_report(make_report_with_explainability())
        service = ReportExportService()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "report.json")
            service.export_json(dto, path)
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)

        assert len(data["narrative_insights"]) == len(dto.narrative_insights)
        for raw, mapped in zip(
            data["narrative_insights"], dto.narrative_insights, strict=True
        ):
            assert raw["source_feature_id"]["feature_type_id"] == (
                mapped.source_feature_id.feature_type_id
            )
            assert raw["source_feature_id"]["semantic_category"] == (
                mapped.source_feature_id.semantic_category
            )
            assert raw["is_traceable"] is True
            assert raw["is_traceable"] is mapped.is_traceable

    def test_export_json_includes_action_origin_fields(self) -> None:
        dto = FinalReportDTO.from_report(make_report_with_explainability())
        service = ReportExportService()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "report.json")
            service.export_json(dto, path)
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)

        assert len(data["coaching_actions"]) == len(dto.coaching_actions)
        for raw, mapped in zip(
            data["coaching_actions"], dto.coaching_actions, strict=True
        ):
            assert raw["origin_feature_type"] == mapped.origin_feature_type
            assert (
                raw["origin_supporting_observation_types"]
                == mapped.origin_supporting_observation_types
            )
            assert (
                raw["origin_objective_description"]
                == mapped.origin_objective_description
            )

    def test_export_pdf_html_payload_includes_explainability(self) -> None:
        dto = FinalReportDTO.from_report(make_report_with_explainability())
        service = ReportExportService()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "report.pdf")
            with patch("services.report_export_service.HTML") as mock_html:
                mock_html.return_value.write_pdf = MagicMock()
                with patch.object(
                    service,
                    "export_pdf",
                    wraps=service.export_pdf,
                ):
                    # Force availability so PDF path exercises HTML builder.
                    with patch(
                        "services.report_export_service._WEASYPRINT_AVAILABLE",
                        True,
                    ):
                        service.export_pdf(dto, path)

                html_arg = mock_html.call_args.kwargs.get("string")
                if html_arg is None:
                    html_arg = mock_html.call_args.args[0]

        assert "Evidence:" in html_arg
        assert "Origin:" in html_arg
        assert dto.narrative_insights[0].prose in html_arg
        assert dto.coaching_actions[0].description in html_arg
        assert dto.coaching_actions[0].origin_objective_description in html_arg

    def test_from_report_remains_sole_factory_for_export_fixture(self) -> None:
        dto = FinalReportDTO.from_report(make_report_with_explainability())
        assert hasattr(FinalReportDTO, "from_report")
        assert not hasattr(FinalReportDTO, "from_components")
        assert isinstance(dto, FinalReportDTO)
