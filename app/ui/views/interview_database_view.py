# app/ui/views/interview_database_view.py

import gradio as gr


class InterviewDatabaseView:
    # Build UI components for database questions

    def build(self):

        with gr.Column(visible=False) as container:

            # ---------------------------------------------------------
            # Display (read-only SQL)
            # ---------------------------------------------------------

            sql_display = gr.Code(
                label="",
                language="sql",
                interactive=False,
                visible=True,
            )

            # ---------------------------------------------------------
            # Input editor (only in QUESTION state)
            # ---------------------------------------------------------

            sql_box = gr.Textbox(
                label="Your SQL",
                elem_id="code-editor",
                lines=10,
                visible=True,
            )

            submit_button = gr.Button("Submit SQL", interactive=False)

        return container, sql_display, sql_box, submit_button
