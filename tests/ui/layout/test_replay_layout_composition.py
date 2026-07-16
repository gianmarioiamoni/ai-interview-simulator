# tests/ui/layout/test_replay_layout_composition.py

from __future__ import annotations

import inspect

import gradio as gr

from app.ui.layout.layout_builder import UILayoutBuilder
from app.ui.layout.sections.report_section import render_report_section
from app.ui.layout.sections.session_history_section import render_session_history_section


def test_report_section_includes_replay_session_button() -> None:
    source = inspect.getsource(render_report_section)
    assert "Replay Session" in source
    assert "replay_session_button" in source


def test_session_history_section_includes_replay_action() -> None:
    with gr.Blocks():
        components = render_session_history_section()
    assert "session_history_dropdown" in components
    assert "replay_from_history_button" in components


def test_layout_builder_wires_replay_and_history() -> None:
    source = inspect.getsource(UILayoutBuilder.build)
    assert "render_replay_section" in source
    assert "render_session_history_section" in source
    assert "REPLAY_LAYOUT_STYLE" in source
    assert "replay_session_button" in source
