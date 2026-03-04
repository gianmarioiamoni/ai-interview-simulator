# app/ui/views/interview_database_view.py

import gradio as gr


class InterviewDatabaseView:

    # Responsible only for building database question UI

    def build(self):

        with gr.Column(visible=False) as container:

            question_text = gr.Markdown("")

            sql_box = gr.Textbox(
                label="Your SQL",
                elem_id="code-editor",
                lines=10,
            )

            submit_button = gr.Button("Submit SQL")

        return container, question_text, sql_box, submit_button
