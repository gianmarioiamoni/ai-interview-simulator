# tests/ui/presentation/test_boundary_error_emission_c3.py
# EPIC-07 P2/C3 — SESSION_START / ANSWER_SUBMIT / NEXT_OR_REPORT emit catalog errors.

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.ui.presentation import (
    AsyncBoundary,
    SurfacePhase,
    emit_boundary_error,
    get_candidate_facing_error_entry,
    present_boundary_failure,
)
from app.ui.state_handlers.navigation import next_question
from app.ui.state_handlers.start import start_interview
from app.ui.state_handlers.submit import submit_answer
from app.ui.ui_response import UIResponse
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import Question, QuestionDifficulty, QuestionType
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.shared.action_type import ActionType
from domain.contracts.user.role import RoleType


def _question() -> Question:
    return Question(
        id="q1",
        prompt="Explain dependency injection.",
        type=QuestionType.WRITTEN,
        area=InterviewArea.TECH_BACKGROUND,
        difficulty=QuestionDifficulty.MEDIUM,
    )


def _interview_state(*, allowed_actions: list[ActionType] | None = None) -> InterviewState:
    state = InterviewState.create_initial(
        role_type=RoleType.BACKEND_ENGINEER,
        interview_type=InterviewType.TECHNICAL,
        company="Acme",
        language="en",
        questions=[_question()],
        interview_id="s1",
        seniority_level="mid",
        interview_length=20,
    )
    if allowed_actions is not None:
        state = state.model_copy(update={"allowed_actions": allowed_actions})
    return state


class TestEmitC3Boundaries:
    @pytest.mark.parametrize(
        ("boundary", "message_key"),
        [
            (AsyncBoundary.SESSION_START, "err.session_start.failed"),
            (AsyncBoundary.ANSWER_SUBMIT, "err.answer_submit.failed"),
            (AsyncBoundary.NEXT_OR_REPORT, "err.next_or_report.failed"),
        ],
    )
    def test_emit_yields_catalog_message(
        self,
        boundary: AsyncBoundary,
        message_key: str,
    ) -> None:
        entry = get_candidate_facing_error_entry(message_key)
        error = emit_boundary_error(boundary)
        assert error.boundary is boundary
        assert error.message_key == message_key
        assert error.message_text == entry.message_text

    def test_present_sets_error_surface_and_message_text(self) -> None:
        response = UIResponse(state=InterviewState.create_empty())
        entry = get_candidate_facing_error_entry("err.next_or_report.failed")
        present_boundary_failure(
            response,
            AsyncBoundary.NEXT_OR_REPORT,
            surface_id="question",
            allows_loader=True,
        )
        assert response.feedback_markdown == entry.message_text
        assert response.candidate_facing_error is not None
        assert response.candidate_facing_error.message_text == entry.message_text
        assert response.surface_state is not None
        assert response.surface_state.phase is SurfacePhase.ERROR
        assert response.surface_state.error is response.candidate_facing_error


class TestHandlerBoundaryFailures:
    def test_next_question_emits_catalog_error_not_silent(self) -> None:
        state = _interview_state(allowed_actions=[ActionType.NEXT])
        entry = get_candidate_facing_error_entry("err.next_or_report.failed")
        response = UIResponse(state=state)

        with patch(
            "app.ui.state_handlers.navigation.run_interview_graph",
            side_effect=RuntimeError("graph boom"),
        ), patch(
            "app.ui.state_handlers.navigation.build_ui_response_from_state",
            return_value=response,
        ), patch(
            "app.ui.state_handlers.navigation.UIOutputAdapter.to_gradio",
            side_effect=lambda r: r,
        ):
            outputs = list(next_question(state))

        assert len(outputs) == 2
        assert response.feedback_markdown == entry.message_text
        assert response.candidate_facing_error is not None
        assert response.candidate_facing_error.boundary is AsyncBoundary.NEXT_OR_REPORT
        assert response.surface_state is not None
        assert response.surface_state.phase is SurfacePhase.ERROR

    def test_submit_answer_emits_catalog_error_not_silent(self) -> None:
        state = _interview_state()
        entry = get_candidate_facing_error_entry("err.answer_submit.failed")
        response = UIResponse(state=state)
        use_case = MagicMock()
        use_case.execute.side_effect = RuntimeError("eval boom")

        with patch(
            "app.ui.state_handlers.submit.get_runtime_llm",
            return_value=MagicMock(),
        ), patch(
            "app.ui.state_handlers.submit.EvaluateAnswerUseCase",
            return_value=use_case,
        ), patch(
            "app.ui.state_handlers.submit.build_ui_response_from_state",
            return_value=response,
        ), patch(
            "app.ui.state_handlers.submit.UIOutputAdapter.to_gradio",
            side_effect=lambda r: r,
        ):
            outputs = list(submit_answer(state, "my answer", "", ""))

        assert len(outputs) >= 2
        assert response.feedback_markdown == entry.message_text
        assert response.candidate_facing_error is not None
        assert response.candidate_facing_error.boundary is AsyncBoundary.ANSWER_SUBMIT
        assert response.surface_state is not None
        assert response.surface_state.phase is SurfacePhase.ERROR

    def test_start_interview_emits_catalog_error_not_silent(self) -> None:
        entry = get_candidate_facing_error_entry("err.session_start.failed")
        recovery = UIResponse(state=InterviewState.create_empty())
        presented: list[UIResponse] = []

        def _capture_to_gradio(response: UIResponse):
            presented.append(response)
            return response

        with patch(
            "app.ui.state_handlers.start.time.sleep",
            return_value=None,
        ), patch(
            "app.ui.state_handlers.start.RoleType",
            side_effect=RuntimeError("start boom"),
        ), patch(
            "app.ui.state_handlers.start.build_ui_response_from_state",
            return_value=recovery,
        ), patch(
            "app.ui.state_handlers.start.UIOutputAdapter.to_gradio",
            side_effect=_capture_to_gradio,
        ):
            outputs = list(
                start_interview(
                    role="backend",
                    role_custom_name="",
                    interview_type="TECHNICAL",
                    seniority="mid",
                    interview_length=20,
                    company="Acme",
                    language="en",
                )
            )

        assert len(outputs) == 2
        final = presented[-1]
        assert final.feedback_markdown == entry.message_text
        assert final.candidate_facing_error is not None
        assert final.candidate_facing_error.boundary is AsyncBoundary.SESSION_START
        assert final.surface_state is not None
        assert final.surface_state.phase is SurfacePhase.ERROR
        assert final.surface_state.surface_id == "setup"
