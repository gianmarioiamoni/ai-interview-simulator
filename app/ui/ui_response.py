# app/ui/ui_response.py

import gradio as gr
from typing import List, Any, Optional
from dataclasses import dataclass

from domain.contracts.feedback.quality import Quality


@dataclass
class UIResponse:

    # ---------------------------------------------------------
    # CORE STATE
    # ---------------------------------------------------------
    state: object

    # ---------------------------------------------------------
    # HEADER
    # ---------------------------------------------------------
    question_counter: str = ""

    # ---------------------------------------------------------
    # FEEDBACK
    # ---------------------------------------------------------
    feedback_markdown: str = ""
    feedback_quality: Optional[Quality] = None

    # ---------------------------------------------------------
    # DISPLAY
    # ---------------------------------------------------------
    written_display: str = ""
    coding_display: str = ""
    database_display: str = ""

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
    next_label: str = "Next Question"

    # ---------------------------------------------------------
    # EDITOR VALUES
    # ---------------------------------------------------------
    written_editor_value: str = ""
    coding_editor_value: str = ""
    database_editor_value: str = ""

    # ---------------------------------------------------------
    # LOADER
    # ---------------------------------------------------------
    loader_visible: bool = False
    loader_value: str = ""

    # ---------------------------------------------------------
    # OUTPUT MAPPING (STRICT CONTRACT)
    # ---------------------------------------------------------
    def to_gradio_outputs(self) -> List[Any]:

        return [
            # -------------------------------------------------
            # STATE
            # -------------------------------------------------
            self.state,
            # -------------------------------------------------
            # HEADER / FEEDBACK
            # -------------------------------------------------
            self.question_counter,
            gr.update(value=self.feedback_markdown),
            # -------------------------------------------------
            # DISPLAY
            # -------------------------------------------------
            self.written_display,
            self.coding_display,
            self.database_display,
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
            gr.update(value=self.written_editor_value),
            gr.update(value=self.coding_editor_value),
            gr.update(value=self.database_editor_value),
            # -------------------------------------------------
            # GLOBAL LOADER (ALWAYS LAST)
            # -------------------------------------------------
            gr.update(
                visible=self.loader_visible,
                value=self.loader_value,
            ),
        ]
