# app/ui/ui_response.py

import gradio as gr
from typing import List, Any
from dataclasses import dataclass


@dataclass
class UIResponse:

    # STATE
    state: object

    # SETUP COMPONENTS
    role_visible: bool = True
    interview_type_visible: bool = True
    company_visible: bool = True
    language_visible: bool = True
    start_button_visible: bool = True

    # TITLE
    page_title: str = "## Configure Your Interview"

    # HEADER
    question_counter: str = ""
    feedback_markdown: str = ""

    # DISPLAY
    written_display: str = ""
    coding_display: str = ""
    database_display: str = ""

    written_visible: bool = False
    coding_visible: bool = False
    database_visible: bool = False

    # REPORT
    final_feedback: str = ""
    report_output: str = ""

    # BUTTONS
    show_submit: bool = False
    submit_interactive: bool = False

    show_retry: bool = False
    retry_interactive: bool = True

    show_next: bool = False

    next_label: str = ""
    submit_label: str = "Submit"

    # EDITORS
    written_editor_value: str = ""
    coding_editor_value: str = ""
    database_editor_value: str = ""

    written_editor_visible: bool = False
    coding_editor_visible: bool = False
    database_editor_visible: bool = False

    # START BUTTON
    start_button_interactive: bool = False

    # LOADER
    loader_visible: bool = False
    loader_value: str = ""

    # OUTPUT CONTRACT
    def to_gradio_outputs(self) -> List[Any]:

        return [
            # 0 STATE
            self.state,
            # 1 SETUP INPUTS
            gr.update(visible=self.role_visible),
            gr.update(visible=self.interview_type_visible),
            gr.update(visible=self.company_visible),
            gr.update(visible=self.language_visible),
            gr.update(
                visible=self.start_button_visible,
                value="Start Interview",
                interactive=self.start_button_interactive,
            ),
            # 8 TITLE
            gr.update(value=self.page_title),
            # 9-10 HEADER
            gr.update(value=self.question_counter),
            gr.update(value=self.feedback_markdown),
            # 11-13 DISPLAY
            gr.update(value=self.written_display, visible=self.written_visible),
            gr.update(value=self.coding_display, visible=self.coding_visible),
            gr.update(value=self.database_display, visible=self.database_visible),
            # 14-15 REPORT
            gr.update(value=self.final_feedback),
            gr.update(value=self.report_output),
            # 16-18 BUTTONS
            gr.update(
                visible=self.show_submit,
                interactive=self.submit_interactive,
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
            # 19-21 EDITORS
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
            # 22 LOADER
            gr.update(
                visible=self.loader_visible,
                value=(
                    f"""
        <div style="
            position: fixed;
            top:0; left:0; right:0; bottom:0;
            background: rgba(0,0,0,0.6);
            display:flex;
            align-items:center;
            justify-content:center;
            backdrop-filter: blur(4px);
            z-index:9999;
        ">
            <div style="
                background: rgba(0,0,0,0.75);
                padding: 20px 30px;
                border-radius: 10px;
                color: white;
                font-size: 18px;
                text-align: center;
            ">
                <div style="
                    border: 4px solid rgba(255,255,255,0.2);
                    border-top: 4px solid white;
                    border-radius: 50%;
                    width: 28px;
                    height: 28px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 10px auto;
                "></div>
                {self.loader_value}
            </div>
        </div>
        """
                    if self.loader_visible
                    else ""
                ),
            ),
        ]
