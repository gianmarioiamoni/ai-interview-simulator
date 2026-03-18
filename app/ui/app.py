# app/ui/app.py

import gradio as gr

from app.ui.layout.ui_layout import build_layout
from app.ui.bindings.ui_bindings import bind_events

def build_app():

    with gr.Blocks(
        css="""
            #code-editor textarea {
                font-family: monospace;
                font-size: 14px;
            }

            #code-editor .cm-content {
                font-family: monospace;
                font-size: 14px;
            }
        """
    ) as demo:

        components = build_layout()

        bind_events(components=components)

    return demo
