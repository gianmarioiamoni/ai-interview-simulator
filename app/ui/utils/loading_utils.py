# app/ui/utils/loading_utils.py

import gradio as gr
from app.ui.components.loader import build_loader_html


def show_loader(message: str = "⏳ Processing..."):
    return gr.update(
        value=build_loader_html(message),
        visible=True,
    )


def hide_loader():
    return gr.update(value="", visible=False)
