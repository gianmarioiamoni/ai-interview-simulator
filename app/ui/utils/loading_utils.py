# app/ui/utils/loading_utils.py

import gradio as gr


def show_loader(message: str = "Processing..."):

    html = f"""
    <div id="loader-root">
        <div class="loader-container">
            <div class="loader-bar"></div>
            <div class="loader-text">⏳ {message}</div>
        </div>
    </div>
    """

    return gr.update(value=html, visible=True)


def hide_loader():
    return gr.update(value="", visible=False)
