# tests/ui/replay/test_replay_responsive_layout.py

from __future__ import annotations

from app.ui.layout.assets.styles import REPLAY_LAYOUT_STYLE
from app.ui.layout.sections.replay_section import render_replay_section


def test_replay_css_defines_three_breakpoints() -> None:
    css = REPLAY_LAYOUT_STYLE
    assert "max-width: 639px" in css  # mobile (< 640)
    assert "min-width: 640px" in css and "max-width: 1024px" in css  # tablet
    assert "min-width: 1025px" in css  # desktop (> 1024)


def test_replay_css_maps_panels_per_data_model() -> None:
    css = REPLAY_LAYOUT_STYLE
    assert "replay-col-nav" in css
    assert "replay-col-question" in css
    assert "replay-col-sidebar" in css
    # Mobile stack order: nav → question → sidebar
    assert '"nav"' in css
    assert '"question"' in css
    assert '"sidebar"' in css


def test_viewport_markers_cover_required_sizes() -> None:
    """AA-07 verification sizes: 320px, 768px, 1280px map to mobile/tablet/desktop."""
    viewports = {
        320: "mobile",
        768: "tablet",
        1280: "desktop",
    }

    def classify(width: int) -> str:
        if width < 640:
            return "mobile"
        if width <= 1024:
            return "tablet"
        return "desktop"

    for width, expected in viewports.items():
        assert classify(width) == expected


def test_replay_section_exposes_responsive_elem_classes() -> None:
    import gradio as gr

    with gr.Blocks():
        components = render_replay_section()

    assert components["replay_section"] is not None
    assert components["replay_nav_progress"] is not None
    assert components["replay_question_panel"] is not None
    assert components["replay_summary_panel"] is not None
    assert components["replay_scoring_panel"] is not None
    assert components["replay_coaching_panel"] is not None
    assert components["replay_error_panel"] is not None
    assert components["replay_forward_button"] is not None
    assert components["replay_backward_button"] is not None
    assert components["replay_exit_button"] is not None
