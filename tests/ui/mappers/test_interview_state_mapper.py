# tests/ui/mappers/test_interview_state_mapper.py
#
# Phase 7C: interview_state_mapper uses FinalReportDTO.from_report(state.report).
# Tests verify stub behavior; full field validation is deferred to Phase 9.

import pytest

from domain.contracts.interview.interview_progress import InterviewProgress

from app.ui.mappers.interview_state_mapper import InterviewStateMapper

from tests.factories.interview_state_factory import (
    build_interview_state,
    build_state_with_execution,
    build_written_question_state,
)
from tests.domain.contracts.report.conftest import make_report


# ---------------------------------------------------------
# SESSION DTO
# ---------------------------------------------------------


def test_session_dto_in_progress_maps_current_question_correctly():

    state = build_interview_state().model_copy(
        update={"progress": InterviewProgress.IN_PROGRESS}
    )

    mapper = InterviewStateMapper()
    dto = mapper.to_session_dto(state)

    assert dto.session_id == state.interview_id
    assert dto.is_completed is False
    assert dto.current_question is not None
    assert dto.current_question.question_id == "q1"
    assert dto.current_question.index == 1
    assert dto.current_question.total == 2
    assert dto.current_area == "Coding"


def test_session_dto_second_question_advances_index():

    state = build_interview_state(current_question_index=1).model_copy(
        update={"progress": InterviewProgress.IN_PROGRESS}
    )

    mapper = InterviewStateMapper()
    dto = mapper.to_session_dto(state)

    assert dto.current_question.question_id == "q2"
    assert dto.current_question.index == 2


def test_session_dto_completed_returns_no_current_question():

    state = build_state_with_execution(passed_tests=2, total_tests=2)

    state = state.model_copy(
        update={
            "progress": InterviewProgress.COMPLETED,
            "current_question_index": len(state.questions),
        }
    )

    mapper = InterviewStateMapper()
    dto = mapper.to_session_dto(state)

    assert dto.is_completed is True
    assert dto.current_question is None
    assert dto.current_area is None


# ---------------------------------------------------------
# FINAL REPORT DTO
# ---------------------------------------------------------


def test_final_report_requires_report():
    """state.report must be set before to_final_report_dto() is called."""
    state = build_interview_state()
    mapper = InterviewStateMapper()
    with pytest.raises(ValueError, match="state.report is required"):
        mapper.to_final_report_dto(state)


def test_final_report_calls_from_report():
    """Phase 9: to_final_report_dto calls FinalReportDTO.from_report(state.report)."""
    from unittest.mock import patch, MagicMock

    state = build_state_with_execution(passed_tests=2, total_tests=2)
    state = state.model_copy(update={"report": make_report()})

    mapper = InterviewStateMapper()
    with patch("app.ui.dto.final_report_dto.FinalReportDTO.from_report") as mock_from_report:
        mock_from_report.return_value = MagicMock()
        result = mapper.to_final_report_dto(state)
    mock_from_report.assert_called_once_with(state.report)
    assert result is mock_from_report.return_value
