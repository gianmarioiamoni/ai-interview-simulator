# app/ui/layout/sections/report_section.py

import gradio as gr


def render_report_section():
    with gr.Group(visible=False) as report_section:
        report_output = gr.HTML("")

        pdf_button = gr.DownloadButton("Download PDF", visible=False)
        json_button = gr.DownloadButton("Download JSON", visible=False)

        replay_session_button = gr.Button(
            "Replay Session",
            visible=True,
            elem_id="replay-session-button",
        )
        new_interview_button = gr.Button("Start New Interview")

    return dict(
        report_section=report_section,
        report_output=report_output,
        pdf_button=pdf_button,
        json_button=json_button,
        replay_session_button=replay_session_button,
        new_interview_button=new_interview_button,
    )
