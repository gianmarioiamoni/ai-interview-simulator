# app/ui/layout/sections/session_history_section.py

from __future__ import annotations

import gradio as gr


def render_session_history_section() -> dict[str, object]:
    """Session history list with Replay action (EPIC-04 C-10 entry path 2)."""

    with gr.Group(visible=True, elem_id="session-history-section") as history_section:
        gr.Markdown("### Session History")
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
        "session_history_dropdown": session_history_dropdown,
        "replay_from_history_button": replay_from_history_button,
    }
