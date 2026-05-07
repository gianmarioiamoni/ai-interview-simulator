# app/ui/ui_response.py

import gradio as gr
from typing import List, Any
from dataclasses import dataclass


@dataclass
class UIResponse:

    # =========================================================
    # STATE
    # =========================================================
    state: object

    # =========================================================
    # SETUP COMPONENTS
    # =========================================================
    role_visible: bool = True
    interview_type_visible: bool = True
    company_visible: bool = True
    language_visible: bool = True
    start_button_visible: bool = True
    start_button_interactive: bool = False

    # =========================================================
    # TITLE
    # =========================================================
    page_title: str = "## Configure Your Interview"

    # =========================================================
    # HEADER
    # =========================================================
    question_counter: str = ""
    feedback_markdown: str = ""

    # =========================================================
    # DISPLAY
    # =========================================================
    written_display: str = ""
    coding_display: str = ""
    database_display: str = ""

    written_visible: bool = False
    coding_visible: bool = False
    database_visible: bool = False

    # =========================================================
    # REPORT
    # =========================================================
    final_feedback: str = ""
    report_output: str = ""

    # =========================================================
    # BUTTONS
    # =========================================================
    show_submit: bool = False
    submit_interactive: bool = False

    show_retry: bool = False
    retry_interactive: bool = True

    show_next: bool = False

    next_label: str = ""
    submit_label: str = "Submit"

    # =========================================================
    # EDITORS
    # =========================================================
    written_editor_value: str = ""
    coding_editor_value: str = ""
    database_editor_value: str = ""

    written_editor_visible: bool = False
    coding_editor_visible: bool = False
    database_editor_visible: bool = False

    # =========================================================
    # LOADER
    # =========================================================
    loader_visible: bool = False
    loader_value: str = ""

    # =========================================================
    # OUTPUT CONTRACT (CRITICO)
    # =========================================================
    def to_gradio_outputs(self) -> List[Any]:
        print("[DEBUG UIResponse] loader_visible:", self.loader_visible)
        print("[DEBUG UIResponse] loader_value:", self.loader_value[:50] if self.loader_value else "")
        return [
            # 0 STATE
            self.state,
            # 1-5 SETUP INPUTS
            gr.update(visible=self.role_visible),
            gr.update(visible=self.interview_type_visible),
            gr.update(visible=self.company_visible),
            gr.update(visible=self.language_visible),
            gr.update(
                visible=self.start_button_visible,
                value="Start Interview",
                interactive=self.start_button_interactive,
            ),
            # 6 TITLE
            gr.update(value=self._build_title_with_loader()),
            # 7-8 HEADER
            gr.update(value=self.question_counter),
            gr.update(value=self.feedback_markdown),
            # 9-11 DISPLAY
            gr.update(value=self.written_display, visible=self.written_visible),
            gr.update(value=self.coding_display, visible=self.coding_visible),
            gr.update(value=self.database_display, visible=self.database_visible),
            # 12-13 REPORT
            gr.update(value=self.final_feedback),
            gr.update(value=self.report_output),
            # 14-16 BUTTONS
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
            # 17-19 EDITORS
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
        ]

    def _build_title_with_loader(self) -> str:

        base = self.page_title or ""

        if not self.loader_visible:
            return base

        return f"""
        {base}

    <div style="
        position: fixed;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(0,0,0,0.6);
        backdrop-filter: blur(4px);
        z-index: 999999;
    ">
        <div style="
            background: rgba(0,0,0,0.85);
            padding: 24px 32px;
            border-radius: 12px;
            color: white;
            font-size: 18px;
            text-align: center;
            min-width: 240px;
        ">
            <div style="
                border: 4px solid rgba(255,255,255,0.2);
                border-top: 4px solid white;
                border-radius: 50%;
                width: 32px;
                height: 32px;
                animation: spin 1s linear infinite;
                margin: 0 auto 12px auto;
            "></div>
            {self.loader_value}
        </div>
    </div>
    """
