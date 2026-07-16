# app/ui/bindings/handlers/replay_layout_coordinator.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import gradio as gr

from app.graph.nodes.replay_node import SessionLoader
from app.ui.replay.panels.replay_error_boundary import ReplayErrorBoundary
from app.ui.replay.replay_context import ReplayContext
from app.ui.replay.replay_entry_point import ReplayEntryPoint
from app.ui.replay.replay_html_composer import (
    compose_error_panel,
    compose_success_panels,
)
from app.ui.replay.replay_view_controller import ReplayViewController
from app.ui.state_machine.ui_state_machine import UIStateMachine
from app.ui.ui_state import UIState
from domain.contracts.interview_state import InterviewState


@dataclass
class ReplayRuntimeState:
    """Ephemeral UI runtime for an active replay (not persisted)."""

    context: ReplayContext
    controller: Optional[ReplayViewController]
    error_boundary: Optional[ReplayErrorBoundary]


@dataclass(frozen=True)
class ReplayLayoutSnapshot:
    """Gradio-facing layout snapshot for the replay view."""

    ui_state: UIState
    replay_section_visible: bool
    report_section_visible: bool
    nav_progress: str
    backward_interactive: bool
    forward_interactive: bool
    question_html: str
    summary_html: str
    scoring_html: str
    coaching_html: str
    error_html: str
    error_visible: bool
    runtime: Optional[ReplayRuntimeState]


class ReplayLayoutCoordinator:
    """Phase 5 layout integration: entry, navigation, exit (ADR-003 / C-01–C-09)."""

    def __init__(self, session_loader: SessionLoader) -> None:
        self._entry = ReplayEntryPoint(session_loader)

    def enter(self, session_id: str) -> ReplayLayoutSnapshot:
        context = ReplayContext(session_id=session_id, is_active=True)
        ui_state = UIStateMachine.resolve(state=None, replay_context=context)
        if ui_state != UIState.REPLAY:
            raise RuntimeError("ReplayContext must resolve to UIState.REPLAY")

        session = self._entry.load(session_id)
        controller, error_boundary = self._entry.route(session)
        runtime = ReplayRuntimeState(
            context=context,
            controller=controller,
            error_boundary=error_boundary,
        )
        return self._snapshot(runtime)

    def navigate_forward(self, runtime: Optional[ReplayRuntimeState]) -> ReplayLayoutSnapshot:
        if runtime is None or runtime.controller is None:
            raise RuntimeError("Cannot navigate without an active ReplayViewController")
        runtime.controller.navigate_forward()
        return self._snapshot(runtime)

    def navigate_backward(self, runtime: Optional[ReplayRuntimeState]) -> ReplayLayoutSnapshot:
        if runtime is None or runtime.controller is None:
            raise RuntimeError("Cannot navigate without an active ReplayViewController")
        runtime.controller.navigate_backward()
        return self._snapshot(runtime)

    def exit(
        self,
        runtime: Optional[ReplayRuntimeState],
        interview_state: InterviewState | None = None,
    ) -> ReplayLayoutSnapshot:
        ui_state = UIStateMachine.resolve(
            state=interview_state,
            replay_context=None,
        )
        return ReplayLayoutSnapshot(
            ui_state=ui_state,
            replay_section_visible=False,
            report_section_visible=True,
            nav_progress="",
            backward_interactive=False,
            forward_interactive=False,
            question_html="",
            summary_html="",
            scoring_html="",
            coaching_html="",
            error_html="",
            error_visible=False,
            runtime=None,
        )

    def _snapshot(self, runtime: ReplayRuntimeState) -> ReplayLayoutSnapshot:
        ui_state = UIStateMachine.resolve(
            state=None,
            replay_context=runtime.context,
        )
        if runtime.error_boundary is not None:
            error_html = compose_error_panel(runtime.error_boundary)
            return ReplayLayoutSnapshot(
                ui_state=ui_state,
                replay_section_visible=True,
                report_section_visible=False,
                nav_progress="",
                backward_interactive=False,
                forward_interactive=False,
                question_html="",
                summary_html="",
                scoring_html="",
                coaching_html="",
                error_html=error_html,
                error_visible=True,
                runtime=runtime,
            )

        if runtime.controller is None:
            raise RuntimeError("Successful replay requires ReplayViewController")

        panels = compose_success_panels(runtime.controller)
        nav = panels["nav"]
        return ReplayLayoutSnapshot(
            ui_state=ui_state,
            replay_section_visible=True,
            report_section_visible=False,
            nav_progress=nav.display_label,
            backward_interactive=nav.backward_enabled,
            forward_interactive=nav.forward_enabled,
            question_html=str(panels["question_html"]),
            summary_html=str(panels["summary_html"]),
            scoring_html=str(panels["scoring_html"]),
            coaching_html=str(panels["coaching_html"]),
            error_html="",
            error_visible=False,
            runtime=runtime,
        )


def snapshot_to_gradio_updates(snapshot: ReplayLayoutSnapshot) -> tuple[object, ...]:
    """Map a layout snapshot to Gradio component updates (replay outputs only)."""
    return (
        snapshot.runtime,
        gr.update(visible=snapshot.replay_section_visible),
        gr.update(visible=snapshot.report_section_visible),
        snapshot.nav_progress,
        gr.update(interactive=snapshot.backward_interactive),
        gr.update(interactive=snapshot.forward_interactive),
        snapshot.question_html,
        snapshot.summary_html,
        snapshot.scoring_html,
        snapshot.coaching_html,
        gr.update(value=snapshot.error_html, visible=snapshot.error_visible),
    )


def resolve_session_id_from_report(state: InterviewState | None) -> str:
    """Derive replay session_id from the completed interview (report entry path)."""
    if state is None:
        raise ValueError("InterviewState is required to start replay from report")
    if state.session_history is not None:
        return state.session_history.session_id
    if state.interview_id:
        return state.interview_id
    raise ValueError("No session_id available for replay")
