# app/ui/utils/loading_utils.py

import gradio as gr


def show_loader(message: str = "⏳ Processing..."):
    return gr.update(value=message, visible=True)


def hide_loader():
    return gr.update(value="", visible=False)
