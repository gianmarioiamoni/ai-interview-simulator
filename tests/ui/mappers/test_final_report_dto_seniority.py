# tests/ui/mappers/test_final_report_dto_seniority.py
#
# Phase 7C: to_final_report_dto() uses from_report() stub.
# Full seniority validation is deferred to Phase 9 (from_report full implementation).

from unittest.mock import patch, MagicMock

from app.ui.mappers.interview_state_mapper import InterviewStateMapper

from tests.factories.interview_state_factory import build_state_with_execution
from tests.domain.contracts.report.conftest import make_report


class TestFinalReportDTOSeniority:

    def test_report_requires_state_report(self):
        """to_final_report_dto raises when state.report is None."""
        import pytest
        state = build_state_with_execution(passed_tests=2, total_tests=2)
        with pytest.raises(ValueError, match="state.report is required"):
            InterviewStateMapper().to_final_report_dto(state)

    def test_report_calls_from_report_with_state_report(self):
        """Phase 7C: to_final_report_dto calls FinalReportDTO.from_report(state.report)."""
        state = build_state_with_execution(passed_tests=2, total_tests=2)
        report = make_report()
        state = state.model_copy(update={"report": report, "seniority_level": "senior"})

        with patch("app.ui.dto.final_report_dto.FinalReportDTO.from_report") as mock_from_report:
            mock_from_report.return_value = MagicMock()
            InterviewStateMapper().to_final_report_dto(state)

        mock_from_report.assert_called_once_with(report)
