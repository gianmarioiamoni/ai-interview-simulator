# Gradio UI composition root

import gradio as gr
from app.ui.components.chat.ChatController import ChatController

def create_app() -> gr.Blocks:
    controller = ChatController()

    with gr.Blocks() as demo:
        gr.Markdown("# GenAI Application")
        controller.render()

    return demo
