# app/ui/layout/sections/session_history_section.py
# EPIC-07 C6 — history list READY/EMPTY/ERROR status surface.

from __future__ import annotations

import gradio as gr

from app.ui.presentation.empty_copy_catalog import get_empty_copy_entry


def render_session_history_section() -> dict[str, object]:
    """Session history list with Replay action (EPIC-04 C-10 + EPIC-07 EC-SH-01)."""

    empty_copy = get_empty_copy_entry("empty.history.none").message_text

    with gr.Group(visible=True, elem_id="session-history-section") as history_section:
        gr.Markdown("### Session History")
        session_history_status = gr.Markdown(
            empty_copy,
            elem_id="session-history-status",
        )
        session_history_dropdown = gr.Dropdown(
            choices=[],
            label="Completed Sessions",
            interactive=True,
            elem_id="session-history-dropdown",
        )
        replay_from_history_button = gr.Button(
            "Replay",
            interactive=False,
            elem_id="replay-from-history",
        )

    return {
        "session_history_section": history_section,
        "session_history_status": session_history_status,
        "session_history_dropdown": session_history_dropdown,
        "replay_from_history_button": replay_from_history_button,
    }
