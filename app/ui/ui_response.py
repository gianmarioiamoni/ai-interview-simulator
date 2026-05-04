import gradio as gr
from typing import List, Any
from dataclasses import dataclass


@dataclass
class UIResponse:

    # ---------------------------------------------------------
    # STATE
    # ---------------------------------------------------------
    state: object

    # ---------------------------------------------------------
    # SETUP (INDIVIDUAL VISIBILITY)
    # ---------------------------------------------------------
    setup_visible: bool = True

    # ---------------------------------------------------------
    # HEADER / FEEDBACK
    # ---------------------------------------------------------
    question_counter: str = ""
    feedback_markdown: str = ""

    # ---------------------------------------------------------
    # DISPLAY
    # ---------------------------------------------------------
    written_display: str = ""
    coding_display: str = ""
    database_display: str = ""

    written_visible: bool = False
    coding_visible: bool = False
    database_visible: bool = False

    # ---------------------------------------------------------
    # REPORT
    # ---------------------------------------------------------
    final_feedback: str = ""
    report_output: str = ""

    # ---------------------------------------------------------
    # BUTTONS
    # ---------------------------------------------------------
    show_submit: bool = False
    show_submit_interactive: bool = False
    show_retry: bool = False
    retry_interactive: bool = True
    show_next: bool = False

    next_label: str = ""
    submit_label: str = "Submit"

    # ---------------------------------------------------------
    # EDITORS
    # ---------------------------------------------------------
    written_editor_value: str = ""
    coding_editor_value: str = ""
    database_editor_value: str = ""

    written_editor_visible: bool = False
    coding_editor_visible: bool = False
    database_editor_visible: bool = False

    # ---------------------------------------------------------
    # LOADER
    # ---------------------------------------------------------
    loader_visible: bool = False
    loader_value: str = ""

    # ---------------------------------------------------------
    # OUTPUT CONTRACT (MATCH UIOutputsBuilder)
    # ---------------------------------------------------------
    def to_gradio_outputs(self) -> List[Any]:

        return [
            # STATE
            self.state,
            # -------------------------------------------------
            # SETUP INPUTS (5 elementi)
            # -------------------------------------------------
            gr.update(visible=self.setup_visible),  # role_input
            gr.update(visible=self.setup_visible),  # interview_type_input
            gr.update(visible=self.setup_visible),  # company_input
            gr.update(visible=self.setup_visible),  # language_input
            gr.update(visible=self.setup_visible),  # start_button
            # -------------------------------------------------
            # HEADER / FEEDBACK
            # -------------------------------------------------
            self.question_counter,
            gr.update(value=self.feedback_markdown),
            # -------------------------------------------------
            # DISPLAY
            # -------------------------------------------------
            gr.update(value=self.written_display, visible=self.written_visible),
            gr.update(value=self.coding_display, visible=self.coding_visible),
            gr.update(value=self.database_display, visible=self.database_visible),
            # -------------------------------------------------
            # REPORT
            # -------------------------------------------------
            self.final_feedback,
            self.report_output,
            # -------------------------------------------------
            # BUTTONS
            # -------------------------------------------------
            gr.update(
                visible=self.show_submit,
                interactive=self.show_submit_interactive,
                value=self.submit_label,
            ),
            gr.update(
                visible=self.show_retry,
                interactive=self.retry_interactive,
            ),
            gr.update(
                visible=self.show_next,
                value=self.next_label,
            ),
            # -------------------------------------------------
            # EDITORS
            # -------------------------------------------------
            gr.update(
                value=self.written_editor_value,
                visible=self.written_editor_visible,
            ),
            gr.update(
                value=self.coding_editor_value,
                visible=self.coding_editor_visible,
            ),
            gr.update(
                value=self.database_editor_value,
                visible=self.database_editor_visible,
            ),
            # -------------------------------------------------
            # LOADER (LAST)
            # -------------------------------------------------
            gr.update(
                visible=self.loader_visible,
                value=self.loader_value,
            ),
        ]
