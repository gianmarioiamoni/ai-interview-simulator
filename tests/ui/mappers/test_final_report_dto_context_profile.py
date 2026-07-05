# tests/ui/mappers/test_final_report_dto_context_profile.py
# Phase 9: to_final_report_dto() uses FinalReportDTO.from_report() — full implementation.

import pytest

from domain.contracts.interview.interview_context_profile import InterviewContextProfile
from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from app.ui.dto.final_report_dto import FinalReportDTO

from tests.factories.interview_state_factory import build_state_with_execution
from tests.domain.contracts.report.conftest import make_report


class TestFinalReportDTOContextProfile:

    def test_report_requires_state_report(self):
        state = build_state_with_execution(passed_tests=2, total_tests=2)
        with pytest.raises(ValueError, match="state.report is required"):
            InterviewStateMapper().to_final_report_dto(state)

    def test_context_profile_sourced_from_report(self):
        """Phase 9: context_profile comes from report.context_profile, not state."""
        state = build_state_with_execution(passed_tests=2, total_tests=2)
        report = make_report()
        state = state.model_copy(update={"report": report})

        dto = InterviewStateMapper().to_final_report_dto(state)

        assert dto.context_profile is report.context_profile

    def test_report_calls_from_report_with_state_report(self):
        """to_final_report_dto calls FinalReportDTO.from_report(state.report)."""
        from unittest.mock import patch, MagicMock

        profile = InterviewContextProfile(job_description="Backend engineer at Big Corp")
        state = build_state_with_execution(passed_tests=2, total_tests=2)
        report = make_report()
        state = state.model_copy(update={"context_profile": profile, "report": report})

        with patch("app.ui.dto.final_report_dto.FinalReportDTO.from_report") as mock_from_report:
            mock_from_report.return_value = MagicMock()
            InterviewStateMapper().to_final_report_dto(state)

        mock_from_report.assert_called_once_with(report)
