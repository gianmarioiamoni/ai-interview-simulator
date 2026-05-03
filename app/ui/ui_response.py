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
    # SECTION VISIBILITY (CRUCIAL)
    # ---------------------------------------------------------
    setup_visible: bool = True
    interview_visible: bool = False
    completion_visible: bool = False
    report_visible: bool = False

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
    # CONTAINERS VISIBILITY
    # ---------------------------------------------------------
    setup_visible: bool = True
    interview_visible: bool = False
    written_visible: bool = False
    coding_visible: bool = False
    database_visible: bool = False

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
        print("\n=== UI RESPONSE OUTPUT ===")
        print("question_counter:", self.question_counter)
        print("written_display:", bool(self.written_display))
        print("coding_display:", bool(self.coding_display))
        print("database_display:", bool(self.database_display))
        print("show_submit:", self.show_submit)
        print("show_retry:", self.show_retry)
        print("show_next:", self.show_next)
        print("==========================\n")

        return [
            # STATE
            self.state,

            # HEADER / FEEDBACK
            self.question_counter,
            gr.update(value=self.feedback_markdown),

            # DISPLAY
            self.written_display,
            self.coding_display,
            self.database_display,
            
            # REPORT
            self.final_feedback,
            self.report_output,
            
            # SECTION VISIBILITY 
            gr.update(visible=self.setup_visible),
            gr.update(visible=self.interview_visible),
            gr.update(visible=self.completion_visible),
            gr.update(visible=self.report_visible),

            # QUESTION TYPE VISIBILITY
            gr.update(visible=self.written_visible),
            gr.update(visible=self.coding_visible),
            gr.update(visible=self.database_visible),

            # BUTTONS
            gr.update(visible=self.show_submit, interactive=self.show_submit_interactive),
            gr.update(visible=self.show_retry, interactive=self.retry_interactive),
            gr.update(visible=self.show_next, value=self.next_label),

            # EDITORS
            gr.update(value=self.written_editor_value),
            gr.update(value=self.coding_editor_value),
            gr.update(value=self.database_editor_value),

            # LOADER
            gr.update(visible=self.loader_visible, value=self.loader_value),
        ]
