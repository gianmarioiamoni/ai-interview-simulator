# app/ui/views/interview_database_view.py

import gradio as gr


class InterviewDatabaseView:

    def build(self):

        with gr.Group(visible=False) as container:  # ✅ FIX

            sql_display = gr.Code(
                label="",
                language="sql",
                interactive=False,
                visible=True,
            )

            sql_box = gr.Code(
                label="Your SQL",
                language="sql",
                interactive=True,
                elem_id="code-editor",
                lines=10,
            )

            submit_button = gr.Button("Submit SQL", interactive=False)

        return container, sql_display, sql_box, submit_button
