# tests/ui/builders/test_ui_response_builder_completion.py

from app.ui.builders.ui_response_builder import UIResponseBuilder
from app.ui.ui_state import UIState
from app.ui.state_machine.ui_state_machine import UIStateMachine
from tests.factories.interview_state_factory import build_interview_state
from tests.factories.question_factory import build_question
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.question.question_evaluation import QuestionEvaluation
from tests.domain.contracts.report.conftest import make_report


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


def test_completion_shows_loading_message_when_processing():
    """I1: Loading message shown when is_processing=True and interview_evaluation=None."""
    builder = UIResponseBuilder()
    state = _completed_state()
    state = state.model_copy(update={"is_processing": True})

    response = builder.build(state)

    assert "please wait" in response.report_output


def test_completion_shows_failure_message_when_not_processing_and_no_evaluation():
    """I1: Failure message shown when processing finished but interview_evaluation is None."""
    builder = UIResponseBuilder()
    state = _completed_state()
    state = state.model_copy(update={"is_processing": False})

    response = builder.build(state)

    assert "failed" in response.report_output.lower()
    assert "new interview" in response.report_output.lower() or "try again" in response.report_output.lower()


def test_a4_report_state_still_renders_report():
    """A4: REPORT state (state.report set) must render the full report (regression guard)."""
    from unittest.mock import patch, MagicMock

    builder = UIResponseBuilder()
    state = _completed_state()

    mock_eval = MagicMock()
    # state.report must be set for UIStateMachine to resolve REPORT state
    state = state.model_copy(update={"interview_evaluation": mock_eval, "report": make_report()})

    with patch("app.ui.builders.ui_response_builder.FinalReportDTO") as mock_dto, \
         patch("app.ui.builders.ui_response_builder.build_report_markdown", return_value="<html>"):
        mock_dto.from_components.return_value = MagicMock()
        response = builder.build(state)

    assert response.page_title == "## Final Report"
    assert response.report_section_visible is True


# ---------------------------------------------------------
# RC1-04 regression tests: state.report as authoritative signal
# ---------------------------------------------------------

def test_rc104_report_state_requires_state_report_for_report_ui_state():
    """RC1-04: UIStateMachine resolves REPORT only when state.report is set."""
    from unittest.mock import MagicMock
    state = _completed_state()
    # Only interview_evaluation set — no state.report → must NOT resolve REPORT
    state = state.model_copy(update={"interview_evaluation": MagicMock()})
    resolved = UIStateMachine.resolve(state)
    assert resolved != UIState.REPORT


def test_rc104_state_report_alone_triggers_report_ui_state():
    """RC1-04: state.report (without interview_evaluation) routes to REPORT state."""
    state = _completed_state()
    state = state.model_copy(update={"report": make_report()})
    resolved = UIStateMachine.resolve(state)
    assert resolved == UIState.REPORT


def test_rc104_state_report_and_evaluation_route_to_report():
    """RC1-04: both state.report and interview_evaluation → REPORT state."""
    from unittest.mock import MagicMock
    state = _completed_state()
    state = state.model_copy(update={"report": make_report(), "interview_evaluation": MagicMock()})
    resolved = UIStateMachine.resolve(state)
    assert resolved == UIState.REPORT


def test_rc104_build_report_shows_unavailable_when_state_report_is_none():
    """RC1-04: _build_report falls back to 'No report available' when state.report is None."""
    from unittest.mock import MagicMock
    builder = UIResponseBuilder()
    state = _completed_state()
    # interview_evaluation is set but state.report is None → no-report fallback
    state = state.model_copy(update={"report": make_report(), "interview_evaluation": None})
    response = builder.build(state)
    assert "No report available" in response.report_output
