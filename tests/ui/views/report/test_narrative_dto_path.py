# tests/ui/views/report/test_narrative_dto_path.py
# EPIC-06 C6 — narrative insights production path is FinalReportDTO-only (OF-01).

from app.ui.dto.final_report_dto import FinalReportDTO, NarrativeInsightDTO
from app.ui.views.report.report_view_model_builder import ReportViewModelBuilder
from app.ui.views.report.sections.narrative_section import render_narrative
from tests.domain.contracts.report.conftest import (
    make_report,
    make_report_with_explainability,
)


class TestNarrativeDtoProductionPath:

    def test_vm_reads_narrative_insights_from_dto(self):
        dto = FinalReportDTO.from_report(make_report_with_explainability())
        assert len(dto.narrative_insights) >= 1

        vm = ReportViewModelBuilder().build(dto)

        assert len(vm["narrative_insights"]) == len(dto.narrative_insights)
        assert all(isinstance(i, NarrativeInsightDTO) for i in vm["narrative_insights"])
        assert (
            vm["narrative_insights"][0].source_feature_id.feature_type_id
            == dto.narrative_insights[0].source_feature_id.feature_type_id
        )
        assert vm["narrative_insights"][0].is_traceable is True

    def test_vm_empty_list_when_dto_insights_empty(self):
        dto = FinalReportDTO.from_report(make_report())
        assert dto.narrative_insights == []

        vm = ReportViewModelBuilder().build(dto)

        assert vm["narrative_insights"] == []

    def test_vm_does_not_read_domain_narrative_fallback(self):
        """DTO-only: empty DTO list must not fall through to Report.narrative.insights."""
        domain_report = make_report_with_explainability()
        dto = FinalReportDTO.from_report(make_report())
        assert dto.narrative_insights == []
        assert len(domain_report.narrative.insights) >= 1

        vm = ReportViewModelBuilder().build(dto)
        assert vm["narrative_insights"] == []

    def test_section_renders_dto_inline_evidence(self):
        dto = FinalReportDTO.from_report(make_report_with_explainability())
        vm = ReportViewModelBuilder().build(dto)
        html = render_narrative(vm)

        assert "Narrative Insights" in html
        assert "Evidence:" in html
        assert "Traceable" in html
        first = dto.narrative_insights[0]
        assert first.prose in html
        assert first.source_feature_id.feature_type_id.replace("_", " ").title() in html
        assert first.source_feature_id.semantic_category.replace("_", " ").title() in html

    def test_section_empty_when_dto_insights_empty(self):
        dto = FinalReportDTO.from_report(make_report())
        vm = ReportViewModelBuilder().build(dto)
        assert render_narrative(vm) == ""

    def test_from_report_remains_sole_factory(self):
        assert hasattr(FinalReportDTO, "from_report")
        assert not hasattr(FinalReportDTO, "from_components")
