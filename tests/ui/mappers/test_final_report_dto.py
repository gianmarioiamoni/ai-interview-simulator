# tests/ui/mappers/test_final_report_dto.py
# EPIC-V13-05 Phase 9 — FinalReportDTO.from_report() architectural tests.

import pytest

from app.ui.dto.final_report_dto import FinalReportDTO
from tests.domain.contracts.report.conftest import make_report


class TestFinalReportDTOFromReport:

    def test_from_components_does_not_exist(self):
        """R-05: from_components must not exist after Phase 9."""
        assert not hasattr(FinalReportDTO, "from_components")

    def test_from_report_exists(self):
        assert hasattr(FinalReportDTO, "from_report")
        assert callable(FinalReportDTO.from_report)

    def test_from_report_returns_final_report_dto(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert isinstance(dto, FinalReportDTO)

    def test_overall_score_from_scoring(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.overall_score == report.scoring.overall_score

    def test_hiring_probability_from_scoring(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.hiring_probability == report.scoring.hiring_probability

    def test_executive_summary_from_scoring_narrative(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.executive_summary == report.scoring_narrative.executive_summary

    def test_gating_triggered_from_scoring(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.gating_triggered == report.scoring.gating_triggered

    def test_percentile_rank_from_scoring(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.percentile_rank == report.scoring.percentile_rank

    def test_dimension_signals_from_scoring(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.dimension_signals == report.scoring.dimension_signals

    def test_weighted_breakdown_from_scoring(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.weighted_breakdown == report.scoring.weighted_breakdown

    def test_dimension_scores_mapped_from_scoring_dimensions(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert len(dto.dimension_scores) == len(report.scoring.scoring_dimensions)

    def test_went_well_from_scoring_narrative(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.went_well == list(report.scoring_narrative.went_well)

    def test_improvement_suggestions_from_scoring_narrative(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.improvement_suggestions == list(report.scoring_narrative.improvement_suggestions)

    def test_seniority_level_from_report(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.seniority_level == report.seniority

    def test_context_profile_from_report(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.context_profile is report.context_profile

    def test_confidence_from_scoring(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.confidence == report.scoring.confidence

    def test_total_tokens_zero_when_no_generation_metadata(self):
        report = make_report()
        assert report.generation_metadata is None
        dto = FinalReportDTO.from_report(report)
        assert dto.total_tokens_used == 0

    def test_question_assessments_count_matches_report(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert len(dto.question_assessments) == len(report.question_assessments)

    def test_raw_score_fallback_to_zero_when_none(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        expected = report.scoring.raw_score if report.scoring.raw_score is not None else 0.0
        assert dto.raw_score == expected

    def test_adjusted_score_fallback_to_overall_when_none(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        expected = (
            report.scoring.adjusted_score
            if report.scoring.adjusted_score is not None
            else report.scoring.overall_score
        )
        assert dto.adjusted_score == expected

    def test_no_interview_state_attributes_accessed(self):
        """Structural: from_report signature takes only Report, no InterviewState."""
        import inspect
        sig = inspect.signature(FinalReportDTO.from_report)
        params = list(sig.parameters.keys())
        assert "state" not in params
        assert "report" in params
