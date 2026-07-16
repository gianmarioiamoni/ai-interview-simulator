# tests/ui/views/report/test_coaching_actions_dto_path.py
# EPIC-06 C7 — coaching actions production path is FinalReportDTO-only (OF-01).

from app.ui.dto.final_report_dto import CoachingActionDTO, FinalReportDTO
from app.ui.views.report.report_view_model_builder import ReportViewModelBuilder
from app.ui.views.report.sections.coaching_section import render_coaching_actions
from tests.domain.contracts.report.conftest import (
    make_report,
    make_report_with_explainability,
)


class TestCoachingActionsDtoProductionPath:

    def test_vm_reads_coaching_actions_from_dto(self):
        dto = FinalReportDTO.from_report(make_report_with_explainability())
        assert len(dto.coaching_actions) >= 1

        vm = ReportViewModelBuilder().build(dto)

        assert len(vm["coaching_actions"]) == len(dto.coaching_actions)
        assert all(isinstance(a, CoachingActionDTO) for a in vm["coaching_actions"])
        first = vm["coaching_actions"][0]
        assert first.origin_feature_type == dto.coaching_actions[0].origin_feature_type
        assert (
            first.origin_objective_description
            == dto.coaching_actions[0].origin_objective_description
        )
        assert (
            first.origin_supporting_observation_types
            == dto.coaching_actions[0].origin_supporting_observation_types
        )

    def test_vm_empty_list_when_dto_actions_empty(self):
        dto = FinalReportDTO.from_report(make_report())
        assert dto.coaching_actions == []

        vm = ReportViewModelBuilder().build(dto)

        assert vm["coaching_actions"] == []

    def test_vm_does_not_read_domain_actions_fallback(self):
        """DTO-only: empty DTO list must not fall through to coaching_snapshot.actions."""
        domain_report = make_report_with_explainability()
        dto = FinalReportDTO.from_report(make_report())
        assert dto.coaching_actions == []
        assert len(domain_report.coaching_snapshot.collection.actions) >= 1

        vm = ReportViewModelBuilder().build(dto)
        assert vm["coaching_actions"] == []

    def test_section_renders_dto_inline_origin(self):
        dto = FinalReportDTO.from_report(make_report_with_explainability())
        vm = ReportViewModelBuilder().build(dto)
        html = render_coaching_actions(vm)

        assert "Coaching Actions" in html
        assert "Origin:" in html
        assert "Supporting observations:" in html
        assert "Objective:" in html
        first = dto.coaching_actions[0]
        assert first.description in html
        assert first.origin_objective_description in html
        assert first.origin_feature_type.replace("_", " ").title() in html

    def test_section_empty_when_dto_actions_empty(self):
        dto = FinalReportDTO.from_report(make_report())
        vm = ReportViewModelBuilder().build(dto)
        assert render_coaching_actions(vm) == ""

    def test_from_report_remains_sole_factory(self):
        assert hasattr(FinalReportDTO, "from_report")
        assert not hasattr(FinalReportDTO, "from_components")

    def test_renderer_composes_coaching_actions(self):
        from app.ui.views.report.report_renderer import ReportRenderer

        dto = FinalReportDTO.from_report(make_report_with_explainability())
        vm = ReportViewModelBuilder().build(dto)
        html = ReportRenderer().render(vm)

        assert "Coaching Actions" in html
        assert "Origin:" in html
        assert dto.coaching_actions[0].description in html
