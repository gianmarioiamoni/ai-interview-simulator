# app/ui/app.py

import gradio as gr

from app.graph.builder import build_graph

from app.ui.layout.ui_layout import build_layout
from app.ui.bindings.ui_bindings import bind_events

def build_app():

    graph = build_graph()

    with gr.Blocks(
        css="""
        #code-editor textarea {
            font-family: monospace;
        }
        """
    ) as demo:

        components = build_layout()

        bind_events(
            graph=graph,
            components=components,
        )

    return demo
