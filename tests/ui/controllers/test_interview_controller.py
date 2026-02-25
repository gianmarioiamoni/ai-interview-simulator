# tests/ui/controllers/test_interview_controller.py

from unittest.mock import Mock

from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.interview_state import InterviewState

from app.ui.controllers.interview_controller import InterviewController
from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.final_report_dto import FinalReportDTO


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def create_mock_state(progress: InterviewProgress) -> InterviewState:
    state = Mock(spec=InterviewState)
    state.progress = progress
    return state


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------


def test_start_interview_invokes_graph_and_returns_session_dto():

    mock_graph = Mock()
    mock_mapper = Mock()

    initial_state = create_mock_state(InterviewProgress.SETUP)
    updated_state = create_mock_state(InterviewProgress.IN_PROGRESS)

    expected_dto = Mock(spec=InterviewSessionDTO)

    mock_graph.invoke.return_value = updated_state
    mock_mapper.to_session_dto.return_value = expected_dto

    controller = InterviewController(mock_graph, mock_mapper)

    result = controller.start_interview(initial_state)

    mock_graph.invoke.assert_called_once_with(initial_state)
    mock_mapper.to_session_dto.assert_called_once_with(updated_state)

    assert result == expected_dto


def test_submit_answer_returns_session_dto_if_not_completed():

    mock_graph = Mock()
    mock_mapper = Mock()

    current_state = create_mock_state(InterviewProgress.IN_PROGRESS)
    updated_state = create_mock_state(InterviewProgress.IN_PROGRESS)

    expected_dto = Mock(spec=InterviewSessionDTO)

    mock_graph.invoke.return_value = updated_state
    mock_mapper.to_session_dto.return_value = expected_dto

    controller = InterviewController(mock_graph, mock_mapper)

    result = controller.submit_answer(current_state)

    mock_graph.invoke.assert_called_once_with(current_state)
    mock_mapper.to_session_dto.assert_called_once_with(updated_state)

    assert result == expected_dto


def test_submit_answer_returns_final_report_when_completed():

    mock_graph = Mock()
    mock_mapper = Mock()

    current_state = create_mock_state(InterviewProgress.IN_PROGRESS)
    completed_state = create_mock_state(InterviewProgress.COMPLETED)

    expected_report = Mock(spec=FinalReportDTO)

    mock_graph.invoke.return_value = completed_state
    mock_mapper.to_final_report_dto.return_value = expected_report

    controller = InterviewController(mock_graph, mock_mapper)

    result = controller.submit_answer(current_state)

    mock_graph.invoke.assert_called_once_with(current_state)
    mock_mapper.to_final_report_dto.assert_called_once_with(completed_state)

    assert result == expected_report
