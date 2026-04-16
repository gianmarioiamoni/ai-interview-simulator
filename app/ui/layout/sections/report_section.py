# app/ui/layout/sections/report_section.py

import gradio as gr


def render_report_section():

    with gr.Column(visible=False) as report_section:

        report_output = gr.HTML("")

        pdf_button = gr.Button("Download PDF")
        json_button = gr.Button("Download JSON")

        pdf_file = gr.File(visible=False, label="Download PDF Report")
        json_file = gr.File(visible=False, label="Download JSON Report")

        new_interview_button = gr.Button("Start New Interview")

    return dict(
        report_section=report_section,
        report_output=report_output,
        pdf_button=pdf_button,
        json_button=json_button,
        pdf_file=pdf_file,
        json_file=json_file,
        new_interview_button=new_interview_button,
    )
