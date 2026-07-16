# tests/ui/replay/test_replay_llm_free.py
# EPIC-04 Phase 6 — AA-02 LLM-free enforcement + read-only / no-persistence gates.

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.ui.bindings.handlers.replay_layout_coordinator import ReplayLayoutCoordinator
from app.ui.replay.panels.replay_coaching_panel import ReplayCoachingPanel
from app.ui.replay.panels.replay_navigation_bar import ReplayNavigationBar
from app.ui.replay.panels.replay_question_panel import ReplayQuestionPanel
from app.ui.replay.panels.replay_scoring_panel import ReplayScoringPanel
from app.ui.replay.panels.replay_session_summary_panel import ReplaySessionSummaryPanel
from app.ui.replay.replay_html_composer import compose_success_panels
from app.ui.replay.replay_view_controller import ReplayViewController
from tests.ui.replay.conftest import (
    make_question_record,
    make_replay_session,
    make_scoring_snapshot,
)


_LLM_PATCH_TARGETS = (
    "services.narrative_generator.narrative_generator.NarrativeGenerator",
    "services.interview_evaluation.generators.narrative_generator.NarrativeGenerator",
    "services.coaching_engine.coaching_engine.CoachingEngine",
    "services.interview_evaluation_service.InterviewEvaluationService",
)


def _run_full_replay_ui_render_path(session) -> None:
    """Traverse the full Replay UI render path (panels + layout composition)."""
    controller = ReplayViewController(session)
    _ = ReplaySessionSummaryPanel(session).render()
    _ = ReplayNavigationBar(session.timeline, controller.current_position).render()
    _ = ReplayQuestionPanel(controller.current_record).render()
    _ = ReplayScoringPanel(session).render()
    _ = ReplayCoachingPanel(session).render()
    _ = compose_success_panels(controller)
    controller.navigate_forward()
    _ = compose_success_panels(controller)


def test_replay_ui_render_path_invokes_no_llm_service() -> None:
    """AA-02: zero LLM service invocations during Replay UI render path."""
    session = make_replay_session(
        question_results=tuple(make_question_record(index=i) for i in range(3)),
        scoring_snapshot=make_scoring_snapshot(),
    )

    mocks: list[MagicMock] = []
    patchers = [patch(target) for target in _LLM_PATCH_TARGETS]
    for patcher in patchers:
        mocks.append(patcher.start())

    try:
        _run_full_replay_ui_render_path(session)
    finally:
        for patcher in patchers:
            patcher.stop()

    for mock_cls in mocks:
        assert mock_cls.call_count == 0
        assert mock_cls.return_value.mock_calls == []


def test_replay_ui_render_path_is_read_only() -> None:
    """Replay UI must not expose re-submission / edit controls (AA-05 / R-11)."""
    session = make_replay_session(
        question_results=tuple(make_question_record(index=i) for i in range(2)),
        scoring_snapshot=make_scoring_snapshot(),
    )
    controller = ReplayViewController(session)
    panels = compose_success_panels(controller)
    html_blob = " ".join(
        [
            str(panels["question_html"]),
            str(panels["summary_html"]),
            str(panels["scoring_html"]),
            str(panels["coaching_html"]),
        ]
    ).lower()

    forbidden_controls = ("submit", "re-submit", "resubmit", "edit answer", "save answer")
    for token in forbidden_controls:
        assert token not in html_blob

    # Session remains frozen / unchanged after render.
    assert session.is_successful is True
    assert len(session.question_results) == 2


def test_replay_ui_path_performs_no_persistence_writes() -> None:
    """Replay UI render path must not write SessionHistory / persistence."""
    session = make_replay_session(
        question_results=(make_question_record(),),
        scoring_snapshot=make_scoring_snapshot(),
    )
    write_mock = MagicMock()

    with (
        patch("builtins.open", write_mock),
        patch("pathlib.Path.write_text", write_mock),
        patch("pathlib.Path.write_bytes", write_mock),
    ):
        _run_full_replay_ui_render_path(session)

    for call in write_mock.mock_calls:
        name = call[0] if call[0] else ""
        # open() may be used for read-only; reject write modes.
        if name == "" and call.args:
            # builtins.open(path, mode=...)
            if len(call.args) >= 2 and isinstance(call.args[1], str):
                assert "w" not in call.args[1] and "a" not in call.args[1]
        assert "write_text" not in name
        assert "write_bytes" not in name


def test_replay_layout_coordinator_enter_invokes_no_llm_service() -> None:
    """AA-02 coverage for layout coordinator enter + first render."""
    session = make_replay_session(
        question_results=tuple(make_question_record(index=i) for i in range(2)),
        scoring_snapshot=make_scoring_snapshot(),
    )
    coordinator = ReplayLayoutCoordinator(session_loader=lambda _sid: None)

    mocks: list[MagicMock] = []
    patchers = [patch(target) for target in _LLM_PATCH_TARGETS]
    for patcher in patchers:
        mocks.append(patcher.start())

    try:
        with patch.object(coordinator._entry, "load", return_value=session):
            snapshot = coordinator.enter(session.session_id)
        assert snapshot.runtime is not None
        assert snapshot.question_html
    finally:
        for patcher in patchers:
            patcher.stop()

    for mock_cls in mocks:
        assert mock_cls.call_count == 0
