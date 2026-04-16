# app/ui/layout/sections/completion_section.py

import gradio as gr


def render_completion_section():

    with gr.Column(visible=False) as completion_section:

        gr.Markdown("## Interview Completed")

        final_feedback = gr.Markdown("")
        view_report_button = gr.Button("View Final Report")

    return dict(
        completion_section=completion_section,
        final_feedback=final_feedback,
        view_report_button=view_report_button,
    )
