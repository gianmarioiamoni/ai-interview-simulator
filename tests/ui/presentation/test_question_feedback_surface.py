# tests/ui/presentation/test_question_feedback_surface.py
# EPIC-07 P4/C8 — question/feedback SurfaceState EMPTY/READY/ERROR wiring.

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.ui.presentation import (
    FEEDBACK_EMPTY_KEY,
    QUESTION_EMPTY_KEY,
    AsyncBoundary,
    ExecutionErrorKind,
    ExecutionErrorPresentation,
    SurfacePhase,
    assert_no_placeholder_chrome,
    emit_boundary_error,
    empty_copy_text,
    format_execution_error_markdown,
    get_empty_copy_entry,
    present_feedback_surface,
    present_question_surface,
    project_execution_error,
    surface_status_message,
)


class TestQuestionSurface:
    def test_ready_when_question_present(self) -> None:
        surface = present_question_surface(has_question=True)
        assert surface.surface_id == "question"
        assert surface.phase is SurfacePhase.READY
        assert surface.empty_copy_key is None
        assert surface.error is None
        assert surface_status_message(surface) == ""

    def test_empty_uses_frozen_catalog_key(self) -> None:
        surface = present_question_surface(has_question=False)
        assert surface.phase is SurfacePhase.EMPTY
        assert surface.empty_copy_key == QUESTION_EMPTY_KEY
        assert surface.empty_copy_key == "empty.question.none"
        text = surface_status_message(surface)
        assert text == get_empty_copy_entry(QUESTION_EMPTY_KEY).message_text
        assert_no_placeholder_chrome(text)

    def test_error_requires_candidate_facing_error(self) -> None:
        error = emit_boundary_error(AsyncBoundary.ANSWER_SUBMIT)
        surface = present_question_surface(has_question=True, error=error)
        assert surface.phase is SurfacePhase.ERROR
        assert surface.error is error
        assert surface_status_message(surface) == error.message_text


class TestFeedbackSurface:
    def test_ready_when_feedback_present(self) -> None:
        surface = present_feedback_surface(has_feedback=True)
        assert surface.surface_id == "feedback"
        assert surface.phase is SurfacePhase.READY
        assert surface.empty_copy_key is None

    def test_empty_uses_frozen_catalog_key(self) -> None:
        surface = present_feedback_surface(has_feedback=False)
        assert surface.phase is SurfacePhase.EMPTY
        assert surface.empty_copy_key == FEEDBACK_EMPTY_KEY
        assert surface.empty_copy_key == "empty.feedback.none"
        text = surface_status_message(surface)
        assert text == get_empty_copy_entry(FEEDBACK_EMPTY_KEY).message_text
        assert_no_placeholder_chrome(text)

    def test_error_uses_boundary_message(self) -> None:
        error = emit_boundary_error(AsyncBoundary.ANSWER_SUBMIT)
        surface = present_feedback_surface(has_feedback=False, error=error)
        assert surface.phase is SurfacePhase.ERROR
        assert surface.empty_copy_key is None
        assert surface_status_message(surface) == error.message_text

    def test_empty_rejects_wrong_catalog_key_via_surface_state(self) -> None:
        with pytest.raises(ValidationError, match="DM-V-SS-02"):
            from app.ui.presentation import SurfaceState

            SurfaceState(
                surface_id="feedback",
                phase=SurfacePhase.EMPTY,
                allows_loader=False,
                empty_copy_key=QUESTION_EMPTY_KEY,
            )


class TestPlaceholderBan:
    @pytest.mark.parametrize(
        "bad",
        [
            "TODO: add feedback",
            "This is a placeholder",
            "Coming soon",
            "<i>internal stub</i>",
            "WIP surface",
        ],
    )
    def test_forbidden_patterns_rejected(self, bad: str) -> None:
        with pytest.raises(ValueError, match="I-SS-03"):
            assert_no_placeholder_chrome(bad)

    def test_catalog_empty_copy_is_finished(self) -> None:
        assert_no_placeholder_chrome(empty_copy_text(QUESTION_EMPTY_KEY))
        assert_no_placeholder_chrome(empty_copy_text(FEEDBACK_EMPTY_KEY))


class TestExecutionErrorMarkdownWiring:
    def test_format_uses_catalog_and_bans_traceback(self) -> None:
        presentation = project_execution_error(
            raw_error=(
                "Traceback (most recent call last):\n"
                '  File "/tmp/main.py", line 1\n'
                "NameError: name 'x' is not defined"
            )
        )
        markdown = format_execution_error_markdown(presentation)
        assert presentation.kind is ExecutionErrorKind.RUNTIME
        assert markdown == presentation.candidate_message
        assert "Traceback" not in markdown
        assert ".py" not in markdown
        assert "NameError" not in markdown
        assert presentation.shows_traceback is False

    def test_detail_lines_rendered_safely(self) -> None:
        presentation = ExecutionErrorPresentation.from_kind(
            ExecutionErrorKind.TEST_FAILURE,
            detail_lines=("case empty",),
        )
        markdown = format_execution_error_markdown(presentation)
        assert "Some tests did not pass." in markdown
        assert "case empty" in markdown
