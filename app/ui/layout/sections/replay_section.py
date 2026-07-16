# app/ui/layout/sections/replay_section.py

from __future__ import annotations

import gradio as gr


def render_replay_section() -> dict[str, object]:
    """Gradio shell for Replay UI (EPIC-04 Phase 5 layout composition)."""

    with gr.Group(visible=False, elem_id="replay-view") as replay_section:
        page_title = gr.Markdown("## Session Replay", elem_classes=["replay-title"])

        with gr.Row(elem_classes=["replay-layout"]):
            with gr.Column(elem_classes=["replay-col-nav"], scale=1):
                nav_progress = gr.Markdown("", elem_id="replay-nav-progress")
                with gr.Row():
                    backward_button = gr.Button(
                        "Previous",
                        interactive=False,
                        elem_id="replay-backward",
                    )
                    forward_button = gr.Button(
                        "Next",
                        interactive=False,
                        elem_id="replay-forward",
                    )

            with gr.Column(elem_classes=["replay-col-question"], scale=2):
                question_panel = gr.HTML("", elem_id="replay-question-panel")

            with gr.Column(elem_classes=["replay-col-sidebar"], scale=1):
                summary_panel = gr.HTML("", elem_id="replay-summary-panel")
                scoring_panel = gr.HTML("", elem_id="replay-scoring-panel")
                coaching_panel = gr.HTML("", elem_id="replay-coaching-panel")

        error_panel = gr.HTML(
            "",
            visible=False,
            elem_id="replay-error-panel",
            elem_classes=["replay-error"],
        )
        exit_button = gr.Button("Exit Replay", elem_id="replay-exit")

    replay_runtime = gr.State(value=None)

    return {
        "replay_section": replay_section,
        "replay_page_title": page_title,
        "replay_nav_progress": nav_progress,
        "replay_backward_button": backward_button,
        "replay_forward_button": forward_button,
        "replay_question_panel": question_panel,
        "replay_summary_panel": summary_panel,
        "replay_scoring_panel": scoring_panel,
        "replay_coaching_panel": coaching_panel,
        "replay_error_panel": error_panel,
        "replay_exit_button": exit_button,
        "replay_runtime": replay_runtime,
    }
