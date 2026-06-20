# tests/ui/builders/test_ui_response_builder_completion.py

from app.ui.builders.ui_response_builder import UIResponseBuilder
from app.ui.ui_state import UIState
from app.ui.state_machine.ui_state_machine import UIStateMachine
from tests.factories.interview_state_factory import build_interview_state
from tests.factories.question_factory import build_question
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.question.question_evaluation import QuestionEvaluation


def _completed_state():
    """Build a state that resolves to UIState.COMPLETION."""
    q = build_question(qid="q1")
    state = build_interview_state(questions=[q])
    return state.model_copy(
        update={
            "is_completed": True,
            "interview_evaluation": None,
        }
    )


def test_a4_completed_state_resolves_to_completion():
    """A4: UIStateMachine must return COMPLETION when is_completed=True and no evaluation."""
    state = _completed_state()
    resolved = UIStateMachine.resolve(state)
    assert resolved == UIState.COMPLETION


def test_a4_ui_response_builder_returns_completion_view():
    """A4: UIResponseBuilder must not fall back to setup screen for COMPLETION."""
    builder = UIResponseBuilder()
    state = _completed_state()

    response = builder.build(state)

    assert response.page_title == "## Interview Complete"
    assert response.start_button_visible is False
    assert response.report_section_visible is True
    assert response.pdf_download_btn_visible is False
    assert response.json_download_btn_visible is False


def test_a4_report_state_still_renders_report():
    """A4: REPORT state must still render the full report (regression guard)."""
    from unittest.mock import patch, MagicMock

    builder = UIResponseBuilder()
    state = _completed_state()

    mock_eval = MagicMock()
    state = state.model_copy(update={"interview_evaluation": mock_eval})

    with patch("app.ui.builders.ui_response_builder.FinalReportDTO") as mock_dto, \
         patch("app.ui.builders.ui_response_builder.build_report_markdown", return_value="<html>"):
        mock_dto.from_components.return_value = MagicMock()
        response = builder.build(state)

    assert response.page_title == "## Final Report"
    assert response.report_section_visible is True
