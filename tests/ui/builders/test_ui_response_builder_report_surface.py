# tests/ui/builders/test_ui_response_builder_report_surface.py
# EPIC-07 P5/C9 — UIResponseBuilder report SurfaceState wiring.

from unittest.mock import patch

from app.ui.builders.ui_response_builder import UIResponseBuilder
from app.ui.presentation import REPORT_EMPTY_KEY, SurfacePhase, get_empty_copy_entry
from tests.domain.contracts.report.conftest import make_report
from tests.factories.interview_state_factory import build_interview_state
from tests.factories.question_factory import build_question


def _report_state(*, processing: bool = False):
    q = build_question(qid="q1")
    state = build_interview_state(questions=[q])
    return state.model_copy(
        update={
            "is_completed": True,
            "report": make_report(),
            "is_processing": processing,
        }
    )


def test_report_dto_ready_not_processing_phase_not_loading() -> None:
    builder = UIResponseBuilder()
    state = _report_state(processing=False)

    with patch(
        "app.ui.builders.ui_response_builder.build_report_markdown",
        return_value="<html>report</html>",
    ), patch(
        "app.ui.builders.ui_response_builder.bind_learning_progress",
        return_value=None,
    ):
        response = builder.build(state)

    assert response.surface_state is not None
    assert response.surface_state.surface_id == "report"
    assert response.surface_state.phase is SurfacePhase.READY
    assert response.surface_state.phase is not SurfacePhase.LOADING
    assert response.loader_visible is False
    assert response.report_section_visible is True


def test_report_dto_ready_processing_still_no_loader() -> None:
    """I-SS-02: DTO ready ∧ even if processing flag set ⇒ phase ≠ LOADING."""
    builder = UIResponseBuilder()
    state = _report_state(processing=True)

    with patch(
        "app.ui.builders.ui_response_builder.build_report_markdown",
        return_value="<html>report</html>",
    ), patch(
        "app.ui.builders.ui_response_builder.bind_learning_progress",
        return_value=None,
    ):
        response = builder.build(state)

    assert response.surface_state is not None
    assert response.surface_state.phase is SurfacePhase.READY
    assert response.surface_state.phase is not SurfacePhase.LOADING
    assert response.loader_visible is False


def test_report_empty_uses_catalog_copy() -> None:
    builder = UIResponseBuilder()
    q = build_question(qid="q1")
    state = build_interview_state(questions=[q])
    state = state.model_copy(update={"is_completed": True, "is_processing": False})
    assert state.report is None

    response = builder._build_report(state)

    assert response.surface_state is not None
    assert response.surface_state.phase is SurfacePhase.EMPTY
    assert response.surface_state.empty_copy_key == REPORT_EMPTY_KEY
    assert response.report_output == get_empty_copy_entry(
        REPORT_EMPTY_KEY
    ).message_text
    assert "<i" not in response.report_output.lower()
    assert "TODO" not in response.report_output
    assert response.loader_visible is False
    assert response.pdf_download_btn_visible is False
